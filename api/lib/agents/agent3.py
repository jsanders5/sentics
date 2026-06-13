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
    """Build Claude prompt for candidate analysis.

    The directional call, timeframe and confidence are already determined
    deterministically by Agent 2. Claude's job is to write a rationale that is
    CONSISTENT with that call — it does not decide the direction itself.
    """
    direction = candidate.get("direction", "Neutral")
    time_horizon = candidate.get("time_horizon", "Medium")
    confidence = candidate.get("confidence_tier", "Low")
    existing_signals = candidate.get("key_signals", [])

    return f"""You are a crypto market analyst. A technical model has already classified this
asset. Write a rationale that explains and is fully consistent with that classification.

ASSET:
- Symbol: {candidate['symbol']}
- Name: {candidate['name']}
- Current Price: ${candidate['price']}

MODEL CLASSIFICATION (do NOT contradict these):
- Direction: {direction}  (price expected to move {'UP' if direction == 'Bullish' else 'DOWN' if direction == 'Bearish' else 'sideways / unclear'})
- Timeframe: {time_horizon}
- Confidence: {confidence}

TECHNICAL INDICATORS:
- RSI (14): {candidate['rsi']}
- Volume Ratio: {candidate['volume_ratio']}x its 30-day average (1.3x = confirmation threshold)
- Technical alignment score: {candidate['technical_score']}/58
- Model-detected signals: {existing_signals}

PROVIDE OUTPUT IN THIS EXACT JSON FORMAT:
{{
  "entry_type": "Breakout|Retest|Dip-Buy",
  "entry_quality": "Strong|Moderate|Speculative",
  "rationale": "2-3 sentences explaining the {direction} thesis over the {time_horizon} timeframe. Cite RSI, volume, and MA structure. Be specific.",
  "key_signals": ["signal1", "signal2", "signal3"]
}}

GUIDELINES:
- The rationale MUST support a {direction} view. If Bearish, explain downside risk; if Bullish, explain upside; if Neutral, explain why the signal is unclear.
- Entry: Breakout if price above both MAs, Retest if pulling back to a MA, Dip-Buy if approaching a MA from below.
- Rationale must be 2-3 sentences max, specific, and cite actual indicator values.
- This is educational analysis, not financial advice.

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
        # Note: direction / time_horizon / confidence_tier are owned by Agent 2
        # and are intentionally NOT returned here so they are never overwritten.
        return {
            "entry_type": parsed.get("entry_type", "Breakout"),
            "entry_quality": parsed.get("entry_quality", "Moderate"),
            "rationale": parsed.get("rationale", "Unable to generate rationale."),
            "key_signals": parsed.get("key_signals", [])
        }
    except Exception as e:
        log_error(f"Error parsing Claude response", e)
        return {
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
                    model="claude-sonnet-4-6",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_text = message.content[0].text

                # Parse response
                analysis = parse_claude_response(response_text)

                # Preserve Agent 2's deterministic key_signals if Claude returned none
                if not analysis.get("key_signals"):
                    analysis.pop("key_signals", None)

                # Merge with candidate data (Agent 2 owns direction/horizon/confidence)
                candidate_with_rationale = {
                    **candidate,
                    **analysis
                }

                candidates_with_rationales.append(candidate_with_rationale)

                log_info(f"Processed {candidate['symbol']}: {candidate.get('confidence_tier', 'Low')} confidence")

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
