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
    insert_pipeline_run, cache_set, cache_invalidate, log_info, log_error
)
from . import agent2, agent3, agent4

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
                "direction": c.get("direction", "Neutral"),
                "time_horizon": c.get("time_horizon", "Medium"),
                "confidence_tier": c.get("confidence_tier", "Low"),
                "score": c.get("candidate_score", 0),
                "rationale": c.get("rationale", ""),
                "entry_type": c.get("entry_type", "Breakout"),
                "entry_quality": c.get("entry_quality", "Moderate"),
                "trade_plan": c.get("trade_plan"),
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
        # Persist the TA candidates immediately. The expensive steps below (Agent 4
        # web search, Agent 3 rationale) can blow past the serverless time limit and
        # get SIGKILL'd with no continuation — this guarantees the dashboard is fresh
        # even if that happens; FA/rationale then enrich it when the run completes.
        log_info("Persisting TA freshness floor...")
        _persist(agent2_result["candidates"])

        # ============ AGENT 4: FUNDAMENTAL ANALYSIS (news/catalyst) ============
        log_info("Running Agent 4 (FA)...")
        agent4_result = agent4.run(agent2_result)
        agent2_result["candidates"] = agent4_result.get("candidates_with_fa", agent2_result["candidates"])

        # ============ AGENT 3: AI SYNTHESIS (FA-aware rationale) ============
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

        # ---- FULL ENRICHED WRITE (TA + FA + rationale) + point-in-time snapshot ----
        _persist(agent3_result.get("candidates_with_rationales", []), fa_snapshot=True)

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
                "agent4": {
                    "status": agent4_result.get("status"),
                    "duration_seconds": agent4_result.get("duration_seconds", 0)
                },
                "agent3": {
                    "status": agent3_result.get("status"),
                    "duration_seconds": agent3_result.get("duration_seconds", 0)
                }
            },
            "summary": {
                "candidates_discovered": agent2_result.get("total_candidates", 0),
                "catalysts_found": agent4_result.get("total_processed", 0) - agent4_result.get("total_failed", 0),
                "rationales_generated": agent3_result.get("total_processed", 0)
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
