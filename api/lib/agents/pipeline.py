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

        # ============ AGENT 4: FUNDAMENTAL ANALYSIS (news/catalyst) ============
        # Scans recent news per coin, scores a catalyst, and blends it into the
        # TA conviction. Degrades gracefully (neutral FA) — never breaks the run.
        log_info("Running Agent 4 (FA)...")
        agent4_result = agent4.run(agent2_result)
        agent2_result["candidates"] = agent4_result.get("candidates_with_fa", agent2_result["candidates"])

        # ============ AGENT 3: AI SYNTHESIS ============
        log_info("Running Agent 3...")
        agent3_result = agent3.run(agent2_result)

        if agent3_result["status"] != "success":
            log_error(f"Agent 3 failed: {agent3_result.get('error')}")
            # Fall back to previous candidates if available
            agent3_result = {
                "status": "partial",
                "candidates_with_rationales": agent2_result.get("candidates", []),
                "total_processed": len(agent2_result.get("candidates", [])),
                "total_failed": 0
            }

        # Persist candidates to database
        candidates_data = [
            {
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
            for c in agent3_result.get("candidates_with_rationales", [])
        ]

        if candidates_data:
            insert_candidates(candidates_data)
            # Prune rows that dropped out of the universe (e.g. stablecoins,
            # coins no longer in the top 25) so the dashboard matches the run.
            delete_candidates_except([c["symbol"] for c in candidates_data])

            # Append-only point-in-time FA log (the leak-free backtest corpus).
            fa_rows = [
                {
                    "symbol": c["symbol"], "name": c.get("name"),
                    "price": c.get("price", 0),
                    "fa_score": c.get("fa_score"), "sentiment": c.get("sentiment"),
                    "magnitude": c.get("magnitude"), "catalyst": c.get("catalyst"),
                    "fa_confidence": c.get("fa_confidence"), "fa_summary": c.get("fa_summary"),
                    "fa_sources": c.get("fa_sources"),
                }
                for c in agent3_result.get("candidates_with_rationales", [])
            ]
            insert_fa_snapshots(fa_rows)
            cache_set("candidates:latest", {
                "timestamp": start_time.isoformat(),
                "candidates": agent3_result.get("candidates_with_rationales", []),
                "count": len(candidates_data)
            }, ttl_minutes=90)
            cache_set("last_update_ts", start_time.isoformat())

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
