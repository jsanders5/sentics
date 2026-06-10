"""
STI Agent Pipeline Orchestrator

Runs Agent 1 → Agent 2 → Agent 3 in sequence.
Persists results to database and cache.
"""

import os
import uuid
from datetime import datetime
from .utils import (
    insert_categories, insert_candidates, insert_pipeline_run,
    cache_set, cache_invalidate, log_info, log_error
)
from . import agent1, agent2, agent3

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

        # ============ AGENT 1: CATEGORY MOMENTUM ============
        log_info("Running Agent 1...")
        agent1_result = agent1.run(trigger_type=trigger_type)

        if agent1_result["status"] != "success":
            raise Exception(f"Agent 1 failed: {agent1_result.get('error')}")

        # Persist categories to database
        insert_categories(agent1_result.get("categories", []))
        cache_set("categories:latest", {
            "timestamp": start_time.isoformat(),
            "categories": agent1_result.get("categories", [])
        }, ttl_minutes=90)

        # ============ AGENT 2: CANDIDATE DISCOVERY ============
        log_info("Running Agent 2...")
        agent2_result = agent2.run(agent1_result)

        if agent2_result["status"] != "success":
            log_error(f"Agent 2 failed: {agent2_result.get('error')}")
            # Continue to Agent 3 with empty candidates
            agent2_result = {
                "status": "partial",
                "candidates": [],
                "total_candidates": 0,
                "low_signal_environment": True
            }

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
                "time_horizon": c.get("time_horizon", "Medium"),
                "confidence_tier": c.get("confidence_tier", "Low"),
                "score": c.get("candidate_score", 0),
                "rationale": c.get("rationale", ""),
                "entry_type": c.get("entry_type", "Breakout"),
                "entry_quality": c.get("entry_quality", "Moderate")
            }
            for c in agent3_result.get("candidates_with_rationales", [])
        ]

        if candidates_data:
            insert_candidates(candidates_data)
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
                "agent1": {
                    "status": agent1_result.get("status"),
                    "duration_seconds": agent1_result.get("duration_seconds", 0)
                },
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
                "categories_scored": len(agent1_result.get("categories", [])),
                "categories_passing": len(agent1_result.get("passing_categories", [])),
                "candidates_discovered": agent2_result.get("total_candidates", 0),
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
