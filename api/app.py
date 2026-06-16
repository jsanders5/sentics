"""Vercel Service: Python agent pipeline.

POST /api/run-pipeline - Trigger the Agent 1 → 2 → 3 pipeline.
  Query params:
    - trigger_type: "scheduled" | "manual" (default: "manual")
"""

import sys
import os

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

# Ensure lib module can be imported - try current directory first, then parent
app_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(app_dir)

# Add both paths to sys.path to handle both local and Vercel environments
sys.path.insert(0, app_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from lib.agents.pipeline import run_pipeline, run_fa_stage

app = FastAPI()


@app.post("/api/run-pipeline")
async def trigger_pipeline(trigger_type: str = Query("manual")):
    """Stage 1: TA + rationale + persist, then fire-and-forget the FA stage."""
    try:
        result = run_pipeline(trigger_type=trigger_type)

        if result.get("status") == "success":
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "run_id": result.get("run_id"),
                    "message": f"Candidates: {result['summary'].get('candidates_discovered', 0)}; FA enrichment running asynchronously.",
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error": result.get("error", "Pipeline execution failed"),
                }
            )
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Pipeline execution failed: {error_msg}", flush=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": error_msg}
        )


@app.post("/api/run-fa")
async def trigger_fa(offset: int = Query(0), batch: int = Query(5)):
    """Stage 2 (chunked, self-chaining): FA-enrich one batch of candidates."""
    try:
        result = run_fa_stage(offset=offset, batch=batch)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] FA stage failed: {error_msg}", flush=True)
        return JSONResponse(status_code=500, content={"status": "error", "error": error_msg})
