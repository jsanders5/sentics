"""
STI Agent Pipeline Orchestrator

Runs Agent 1 → Agent 2 → Agent 3 in sequence.
Persists results to database and cache.
"""

import os
import uuid
from datetime import datetime
from typing import Dict
from .utils import (
    insert_candidates, delete_candidates_except, insert_fa_snapshots,
    insert_call_snapshots, get_candidates, update_candidate_fa, trigger_async,
    insert_pipeline_run, cache_set, cache_invalidate, log_info, log_error
)
from . import agent2, agent3, agent4

# FA stage runs in small self-chaining batches so no single serverless invocation
# exceeds the function time limit (web search is slow).
FA_BATCH = 5

def run_pipeline(trigger_type: str = "scheduled") -> Dict:
    """
    Execute full Agent 1 → 2 → 3 pipeline.

    Args:
    - trigger_type: "scheduled" or "manual"

    Returns:
    {
        "run_id": "...",
        "status": "success" | "error",
        "trigger_type": "scheduled" | "manual",
        "timestamps": {
            "start": "2026-06-10T15:00:00Z",
            "end": "2026-06-10T15:02:30Z"
        },
        "agents": {
            "agent1": {...},
            "agent2": {...},
            "agent3": {...}
        },
        "summary": {
            "categories_scored": X,
            "categories_passing": X,
            "candidates_discovered": X,
            "rationales_generated": X
        }
    }
    """
    from datetime import datetime

    run_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    try:
        log_info(f"Pipeline starting: {run_id} ({trigger_type})")

        # ============ AGENT 2: TOP-25 MARKET ANALYSIS ============
        # Agent 1 (category momentum) was retired — the pipeline now analyzes
        # the top 25 coins by market cap directly.
        log_info("Running Agent 2...")
        agent2_result = agent2.run()

        if agent2_result["status"] != "success":
            log_error(f"Agent 2 failed: {agent2_result.get('error')}")
            # Continue to Agent 3 with empty candidates
            agent2_result = {
                "status": "partial",
                "candidates": [],
                "total_candidates": 0,
                "low_signal_environment": True
            }

        def _candidate_row(c):
            return {
                "symbol": c["symbol"],
                "name": c["name"],
                "category": c.get("category"),
                "market_cap": c.get("market_cap", 0),
                "price": c.get("price", 0),
                "rsi": c.get("rsi", 0),
                "volume_ratio": c.get("volume_ratio", 0),
                "technical_score": c.get("technical_score", 0),
                "category_momentum": c.get("category_momentum", 0),
                "directional_score": c.get("directional_score", 0),
                "direction": c.get("direction", "Neutral"),
                "time_horizon": c.get("time_horizon", "Medium"),
                "confidence_tier": c.get("confidence_tier", "Low"),
                "score": c.get("candidate_score", 0),
                "rationale": c.get("rationale", ""),
                "entry_type": c.get("entry_type", "Breakout"),
                "entry_quality": c.get("entry_quality", "Moderate"),
                "trade_plan": c.get("trade_plan"),
                "ohlc": c.get("ohlc"),
                "tv_symbol": c.get("tv_symbol"),
                "fa_score": c.get("fa_score"),
                "sentiment": c.get("sentiment"),
                "catalyst": c.get("catalyst"),
                "fa_summary": c.get("fa_summary"),
                "fa_confidence": c.get("fa_confidence"),
                "fa_sources": c.get("fa_sources"),
            }

        def _persist(candidates, fa_snapshot=False):
            """Write candidates (upsert), prune dropped symbols, refresh freshness.
            Called twice: a cheap TA 'floor' right after Agent 2, then the full
            enriched write after FA + rationale — so a later timeout can't leave
            the dashboard stale."""
            rows = [_candidate_row(c) for c in candidates]
            if not rows:
                return
            insert_candidates(rows)
            delete_candidates_except([r["symbol"] for r in rows])
            if fa_snapshot:
                insert_fa_snapshots([
                    {
                        "symbol": c["symbol"], "name": c.get("name"), "price": c.get("price", 0),
                        "fa_score": c.get("fa_score"), "sentiment": c.get("sentiment"),
                        "magnitude": c.get("magnitude"), "catalyst": c.get("catalyst"),
                        "fa_confidence": c.get("fa_confidence"), "fa_summary": c.get("fa_summary"),
                        "fa_sources": c.get("fa_sources"),
                    }
                    for c in candidates
                ])
            cache_set("candidates:latest", {
                "timestamp": start_time.isoformat(), "candidates": candidates, "count": len(rows),
            }, ttl_minutes=90)
            cache_set("last_update_ts", start_time.isoformat())

        # ---- FRESHNESS FLOOR ----
        # Persist TA candidates immediately, so even if Agent 3 is slow and the
        # function is SIGKILL'd at the time limit, the dashboard is still fresh.
        log_info("Persisting TA freshness floor...")
        _persist(agent2_result["candidates"])

        # ============ AGENT 3: AI SYNTHESIS (rationale on TA) ============
        log_info("Running Agent 3...")
        agent3_result = agent3.run(agent2_result)
        if agent3_result["status"] != "success":
            log_error(f"Agent 3 failed: {agent3_result.get('error')}")
            agent3_result = {
                "status": "partial",
                "candidates_with_rationales": agent2_result.get("candidates", []),
                "total_processed": len(agent2_result.get("candidates", [])),
                "total_failed": 0,
            }

        # Full TA + rationale write (FA is added later by the chunked FA stage).
        final_candidates = agent3_result.get("candidates_with_rationales", [])
        _persist(final_candidates)

        # ---- LIVE FORWARD-TRACKING LEDGER ----
        # Append an immutable, point-in-time row per directional call (price/levels
        # as shown now). eval_calls.py scores these against realized forward prices
        # later — the leak-free ground truth for whether the calls have live edge.
        run_ts = start_time.isoformat()
        call_rows = []
        for c in final_candidates:
            if c.get("direction") not in ("Bullish", "Bearish"):
                continue
            plan = c.get("trade_plan") or {}
            call_rows.append({
                "run_ts": run_ts,
                "symbol": c.get("symbol"),
                "name": c.get("name"),
                "direction": c.get("direction"),
                "candidate_score": c.get("candidate_score"),
                "confidence_tier": c.get("confidence_tier"),
                "time_horizon": c.get("time_horizon"),
                "directional_score": c.get("directional_score"),
                "price": c.get("price"),
                "entry": plan.get("entry"),
                "target": plan.get("target"),
                "stop": plan.get("stop"),
                "fa_score": c.get("fa_score"),
            })
        insert_call_snapshots(call_rows)

        # ---- TRIGGER STAGE 2 (FA), fire-and-forget ----
        # FA (web search) is too slow to fit this invocation, so it runs as its own
        # self-chaining batched stage that PATCHes FA onto the rows we just wrote.
        directional = sum(1 for c in agent2_result["candidates"]
                          if c.get("direction") in ("Bullish", "Bearish"))
        if directional:
            # Drop any prior run's news snapshot so this run's FA batches all fetch
            # + share a fresh point-in-time snapshot (see agent4.FEED_CACHE_KEY).
            cache_invalidate(agent4.FEED_CACHE_KEY)
            log_info(f"Triggering FA stage for {directional} directional candidates...")
            trigger_async("/api/run-fa", {"offset": 0, "batch": FA_BATCH})

        # Invalidate old cache if needed
        cache_invalidate("candidates:stale", "categories:stale")

        # Log pipeline run
        end_time = datetime.utcnow()
        insert_pipeline_run(
            run_id=run_id,
            trigger_type=trigger_type,
            status="success"
        )

        log_info(f"Pipeline complete: {run_id}")

        return {
            "run_id": run_id,
            "status": "success",
            "trigger_type": trigger_type,
            "timestamps": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "agents": {
                "agent2": {
                    "status": agent2_result.get("status"),
                    "duration_seconds": agent2_result.get("duration_seconds", 0)
                },
                "agent3": {
                    "status": agent3_result.get("status"),
                    "duration_seconds": agent3_result.get("duration_seconds", 0)
                }
            },
            "summary": {
                "candidates_discovered": agent2_result.get("total_candidates", 0),
                "rationales_generated": agent3_result.get("total_processed", 0),
                "fa_stage": "triggered (async, chunked)"
            }
        }

    except Exception as e:
        log_error("Pipeline failed", e)
        end_time = datetime.utcnow()

        try:
            insert_pipeline_run(
                run_id=run_id,
                trigger_type=trigger_type,
                status="error",
                error_msg=str(e)
            )
        except:
            pass

        return {
            "run_id": run_id,
            "status": "error",
            "error": str(e),
            "trigger_type": trigger_type,
            "timestamps": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }


def run_fa_stage(offset: int = 0, batch: int = FA_BATCH) -> Dict:
    """Stage 2 (chunked): FA-score one batch of directional candidates loaded from
    the DB, PATCH FA + re-blended conviction onto those rows, append point-in-time
    snapshots, then fire-and-forget the next batch. Small batches keep each
    invocation well under the serverless time limit, so FA reliably completes."""
    try:
        rows = get_candidates()
        directional = sorted(
            [r for r in rows if r.get("direction") in ("Bullish", "Bearish")],
            key=lambda r: r.get("symbol", ""),  # deterministic order across invocations
        )
        total = len(directional)
        chunk = directional[offset:offset + batch]
        if not chunk:
            log_info(f"FA stage: nothing to do at offset {offset}/{total}")
            return {"status": "success", "processed": 0, "offset": offset, "total": total}

        log_info(f"FA stage: scoring {offset}-{offset + len(chunk)} of {total} directional candidates")
        scored = agent4.score_candidates(chunk)

        snapshots = []
        for c in scored:
            update_candidate_fa(c["symbol"], {
                "fa_score": c.get("fa_score"),
                "sentiment": c.get("sentiment"),
                "catalyst": c.get("catalyst"),
                "fa_summary": c.get("fa_summary"),
                "fa_confidence": c.get("fa_confidence"),
                "fa_sources": c.get("fa_sources"),
                "score": c.get("candidate_score"),  # re-blended TA+FA conviction
            })
            snapshots.append({
                "symbol": c["symbol"], "name": c.get("name"), "price": c.get("price"),
                "fa_score": c.get("fa_score"), "sentiment": c.get("sentiment"),
                "magnitude": c.get("magnitude"), "catalyst": c.get("catalyst"),
                "fa_confidence": c.get("fa_confidence"), "fa_summary": c.get("fa_summary"),
                "fa_sources": c.get("fa_sources"),
            })
        insert_fa_snapshots(snapshots)

        next_offset = offset + batch
        if next_offset < total:
            trigger_async("/api/run-fa", {"offset": next_offset, "batch": batch})
            log_info(f"FA stage: chained next batch at offset {next_offset}")
        else:
            log_info(f"FA stage complete: {total} directional candidates enriched")

        return {
            "status": "success",
            "processed": len(scored),
            "offset": offset,
            "total": total,
            "next_offset": next_offset if next_offset < total else None,
        }
    except Exception as e:
        log_error("FA stage failed", e)
        return {"status": "error", "error": str(e), "offset": offset}
