"""
Vercel Python Function: POST /api/run-pipeline

Triggers the full Agent 1 → 2 → 3 pipeline.

Query params:
- trigger_type: "scheduled" | "manual" (default: "manual")

Response:
{
  "status": "success" | "error",
  "run_id": "uuid",
  "message": "Pipeline execution details",
  "error": "error message (if failed)"
}
"""

import os
import sys
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add project root to path so we can import agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.agents.pipeline import run_pipeline


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests to trigger the pipeline."""
        try:
            # Parse query params
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            trigger_type = query_params.get("trigger_type", ["manual"])[0]

            # Run the pipeline
            result = run_pipeline(trigger_type=trigger_type)

            # Prepare response
            if result.get("status") == "success":
                response_data = {
                    "status": "success",
                    "run_id": result.get("run_id"),
                    "message": f"Pipeline complete. Categories: {result['summary'].get('categories_passing', 0)}/{result['summary'].get('categories_scored', 0)}, Candidates: {result['summary'].get('rationales_generated', 0)}",
                }
                status_code = 200
            else:
                response_data = {
                    "status": "error",
                    "error": result.get("error", "Pipeline execution failed"),
                }
                status_code = 500

            # Send response
            self.send_response(status_code)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Pipeline execution failed: {error_msg}", flush=True)

            response_data = {
                "status": "error",
                "error": error_msg,
            }

            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
