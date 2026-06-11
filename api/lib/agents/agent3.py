"""
Agent 3: Forward-Looking Synthesis with Claude

Takes candidate list from Agent 2 and generates AI-powered analysis:
- Time horizon prediction (Short: 1-7d, Medium: 1-4w, Long: 1-3mo)
- Confidence tier (High, Medium, Low)
- Detailed rationale (cites technical + narrative signals)
- Entry type (Breakout, Retest, Dip-Buy)

Uses Anthropic Claude API for high-quality synthesis.

Output: Ranked candidates with rationales, ready for dashboard
"""

import os
import json
from typing import List, Dict
import anthropic

from .utils import log_info, log_error

def get_recent_news(coin_id: str) -> str:
    """
    Fetch recent news for a coin.
    (Placeholder - would integrate with NewsAPI or similar)
    """
    return "No recent major news detected."

def build_prompt(candidate: Dict, agent2_data: Dict) -> str:
    """Build Claude prompt for candidate analysis."""
    return f"""Analyze this cryptocurrency trading candidate and provide structured output.

CANDIDATE DATA:
- Symbol: {candidate['symbol']}
- Name: {candidate['name']}
- Category: {candidate['category']}
- Current Price: ${candidate['price']}
- Technical Score: {candidate['technical_score']}/58
- Category Momentum: {candidate['category_momentum']}/100
- Candidate Score: {candidate['candidate_score']}/100

TECHNICAL INDICATORS:
- RSI (14): {candidate['rsi']} (bullish range: 40-72)
- Volume Ratio: {candidate['volume_ratio']}x (threshold: 1.3x)
- Above 20d & 50d MAs: Yes (required filter)

PROVIDE OUTPUT IN THIS EXACT JSON FORMAT:
{{
  "time_horizon": "Short|Medium|Long",
  "confidence_tier": "High|Medium|Low",
  "entry_type": "Breakout|Retest|Dip-Buy",
  "entry_quality": "Strong|Moderate|Speculative",
  "rationale": "2-3 sentences explaining the thesis. Cite the RSI, volume, and category momentum. Be specific about why this setup is compelling.",
  "key_signals": ["signal1", "signal2", "signal3"]
}}

GUIDELINES:
- Time horizon: Short if RSI > 65 (overbought momentum), Medium if technical + category strong, Long if structural trend
- Confidence: High if 3+ signals strong, Medium if 2 signals strong, Low if mixed signals
- Entry: Breakout if price above both MAs, Retest if pullback to MA, Dip-Buy if approaching MA from below
- Meme coins ({candidate['category']}): cap at Medium confidence regardless of score
- Rationale must be 2-3 sentences max, specific, and cite actual indicators

Return ONLY valid JSON, no markdown or extra text.
"""

def parse_claude_response(response_text: str) -> Dict:
    """Parse Claude's JSON response."""
    try:
        # Claude might return markdown code blocks; extract JSON
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        parsed = json.loads(json_str)
        return {
            "time_horizon": parsed.get("time_horizon", "Medium"),
            "confidence_tier": parsed.get("confidence_tier", "Low"),
            "entry_type": parsed.get("entry_type", "Breakout"),
            "entry_quality": parsed.get("entry_quality", "Moderate"),
            "rationale": parsed.get("rationale", "Unable to generate rationale."),
            "key_signals": parsed.get("key_signals", [])
        }
    except Exception as e:
        log_error(f"Error parsing Claude response", e)
        return {
            "time_horizon": "Medium",
            "confidence_tier": "Low",
            "entry_type": "Breakout",
            "entry_quality": "Moderate",
            "rationale": "Analysis generation failed.",
            "key_signals": []
        }

def run(agent2_result: Dict) -> Dict:
    """
    Run Agent 3: AI Synthesis

    Args:
    - agent2_result: Output from Agent 2 (list of candidates)

    Returns:
    {
        "status": "success" | "error",
        "candidates_with_rationales": [
            {
                ...candidate fields from Agent 2...
                "time_horizon": "Short|Medium|Long",
                "confidence_tier": "High|Medium|Low",
                "entry_type": "Breakout|Retest|Dip-Buy",
                "entry_quality": "Strong|Moderate|Speculative",
                "rationale": "...",
                "key_signals": [...]
            },
            ...
        ],
        "total_processed": X,
        "total_failed": X,
        "duration_seconds": X
    }
    """
    import time
    start_time = time.time()

    try:
        log_info("Agent 3 starting: AI Synthesis")

        candidates = agent2_result.get("candidates", [])
        if not candidates:
            log_info("No candidates from Agent 2; skipping Agent 3")
            return {
                "status": "success",
                "candidates_with_rationales": [],
                "total_processed": 0,
                "total_failed": 0,
                "duration_seconds": 0
            }

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY not set")
        client = anthropic.Anthropic(api_key=api_key)

        candidates_with_rationales = []
        failed_count = 0

        # Process up to 25 candidates (cost control)
        for candidate in candidates[:25]:
            try:
                # Build prompt
                prompt = build_prompt(candidate, agent2_result)

                # Call Claude API
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_text = message.content[0].text

                # Parse response
                analysis = parse_claude_response(response_text)

                # Merge with candidate data
                candidate_with_rationale = {
                    **candidate,
                    **analysis
                }

                candidates_with_rationales.append(candidate_with_rationale)

                log_info(f"Processed {candidate['symbol']}: {analysis['confidence_tier']} confidence")

            except Exception as e:
                log_error(f"Error processing {candidate['symbol']}", e)
                failed_count += 1
                continue

        # Sort by candidate score descending
        candidates_with_rationales.sort(key=lambda x: x["candidate_score"], reverse=True)

        log_info(f"Agent 3 complete: {len(candidates_with_rationales)} rationales generated, {failed_count} failed")

        return {
            "status": "success" if failed_count == 0 else "partial",
            "candidates_with_rationales": candidates_with_rationales,
            "total_processed": len(candidates_with_rationales),
            "total_failed": failed_count,
            "duration_seconds": round(time.time() - start_time, 2)
        }

    except Exception as e:
        log_error("Agent 3 failed", e)
        return {
            "status": "error",
            "error": str(e),
            "candidates_with_rationales": [],
            "total_processed": 0,
            "total_failed": 0,
            "duration_seconds": round(time.time() - start_time, 2)
        }
