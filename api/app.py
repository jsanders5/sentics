"""Vercel Service: Python agent pipeline.

POST /api/run-pipeline - Trigger the Agent 1 → 2 → 3 pipeline.
  Query params:
    - trigger_type: "scheduled" | "manual" (default: "manual")
"""

import sys
import os

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

# Ensure lib module can be imported from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.agents.pipeline import run_pipeline

app = FastAPI()


@app.post("/api/run-pipeline")
async def trigger_pipeline(trigger_type: str = Query("manual")):
    """Trigger the pipeline execution."""
    try:
        result = run_pipeline(trigger_type=trigger_type)

        if result.get("status") == "success":
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "run_id": result.get("run_id"),
                    "message": f"Pipeline complete. Categories: {result['summary'].get('categories_passing', 0)}/{result['summary'].get('categories_scored', 0)}, Candidates: {result['summary'].get('rationales_generated', 0)}",
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
            content={
                "status": "error",
                "error": error_msg,
            }
        )
