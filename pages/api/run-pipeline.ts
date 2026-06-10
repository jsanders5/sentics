import { NextApiRequest, NextApiResponse } from 'next';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';

const execAsync = promisify(exec);

type ResponseData = {
  status: string;
  message?: string;
  run_id?: string;
  error?: string;
};

/**
 * POST /api/run-pipeline
 *
 * Triggers the full Agent 1 → 2 → 3 pipeline.
 *
 * Query params:
 * - trigger_type: "scheduled" | "manual" (default: "manual")
 *
 * Response:
 * {
 *   "status": "success" | "error",
 *   "run_id": "uuid",
 *   "message": "Pipeline execution details"
 * }
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ status: 'error', message: 'Method not allowed' });
  }

  try {
    const trigger_type = (req.query.trigger_type as string) || 'manual';

    // Get the project root (parent of pages directory)
    const projectRoot = path.resolve(process.cwd());

    // Create a temporary Python script to run the pipeline
    const scriptContent = `
import sys
sys.path.insert(0, '${projectRoot}')

from lib.agents.pipeline import run_pipeline
import json

result = run_pipeline(trigger_type='${trigger_type}')
print(json.dumps(result))
`;

    const tempScriptPath = path.join(projectRoot, 'tmp_pipeline_runner.py');
    fs.writeFileSync(tempScriptPath, scriptContent);

    // Execute the Python script
    const { stdout, stderr } = await execAsync(
      `python ${tempScriptPath}`,
      {
        cwd: projectRoot,
        env: {
          ...process.env,
          DATABASE_URL: process.env.DATABASE_URL,
          REDIS_URL: process.env.REDIS_URL,
          SENTRY_DSN: process.env.SENTRY_DSN,
          ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
        },
        timeout: 600000, // 10 minutes
      }
    );

    // Clean up temp file
    fs.unlinkSync(tempScriptPath);

    // Parse output
    const result = JSON.parse(stdout.trim());

    if (result.status === 'success') {
      return res.status(200).json({
        status: 'success',
        run_id: result.run_id,
        message: `Pipeline complete. Categories: ${result.summary.categories_passing}/${result.summary.categories_scored}, Candidates: ${result.summary.rationales_generated}`,
      });
    } else {
      return res.status(500).json({
        status: 'error',
        error: result.error || 'Pipeline execution failed',
      });
    }
  } catch (error) {
    console.error('Pipeline error:', error);
    return res.status(500).json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
