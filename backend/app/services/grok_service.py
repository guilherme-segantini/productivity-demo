"""Grok/LiteLLM service for AI-powered radar analysis."""

import json
import os
from datetime import datetime, timezone
from typing import Optional

import litellm
from dotenv import load_dotenv

load_dotenv()

FOCUS_AREAS = {
    "voice_ai_ux": {
        "name": "Voice AI UX",
        "evaluation_criteria": """
- Latency benchmarks (target: sub-200ms voice-to-voice)
- Interruption handling and VAD (Voice Activity Detection) implementation
- WebRTC/streaming architecture details
- SDK availability and async streaming support
""",
    },
    "agent_orchestration": {
        "name": "Agent Orchestration",
        "evaluation_criteria": """
- BKG/Knowledge Graph integration capabilities
- Tool chaining patterns and workflow composition
- State persistence and checkpoint/recovery mechanisms
- Human-in-the-loop specifications
""",
    },
    "durable_runtime": {
        "name": "Durable Runtime",
        "evaluation_criteria": """
- Durability guarantees and SLAs
- Cold-start benchmarks (target: <100ms)
- Checkpoint/recovery specifications
- Fault tolerance and automatic retry mechanisms
""",
    },
}

DISCOVERY_PROMPT_TEMPLATE = """Using your real-time knowledge of X/Twitter discussions and tech news from the past 7 days,
SEARCH for and ANALYZE tools related to {focus_area}.

STEP 1 - DISCOVER:
Search your knowledge for tools being discussed in the {focus_area_name} space.
Look for announcements, releases, technical discussions, and trending topics.

STEP 2 - CLASSIFY each discovered tool as SIGNAL or NOISE:

SIGNAL criteria (worth evaluating):
- Has published benchmarks or performance data
- Shows production usage or real case studies
- Provides specific technical architecture details
- Has active technical community discussion

NOISE criteria (skip):
- Uses marketing language without substance
- No benchmarks or only vague claims
- Pre-announcement hype or vaporware
- Engagement farming without technical depth

For {focus_area_name}, specifically evaluate:
{evaluation_criteria}

Return a JSON array with 2-4 tools (mix of signal and noise). Format:
[
  {{
    "tool_name": "string",
    "classification": "signal" or "noise",
    "confidence_score": 1-100,
    "technical_insight": "specific technical details you found",
    "signal_evidence": ["evidence1", "evidence2"],
    "noise_indicators": ["indicator1", "indicator2"],
    "architectural_verdict": true or false
  }}
]

IMPORTANT: Return ONLY the JSON array, no other text."""


def analyze_focus_area(focus_area: str) -> Optional[list[dict]]:
    """
    Analyze a single focus area using Grok via LiteLLM.

    Returns list of trend dictionaries or None if analysis fails.
    """
    if focus_area not in FOCUS_AREAS:
        raise ValueError(f"Unknown focus area: {focus_area}")

    area_config = FOCUS_AREAS[focus_area]
    prompt = DISCOVERY_PROMPT_TEMPLATE.format(
        focus_area=focus_area,
        focus_area_name=area_config["name"],
        evaluation_criteria=area_config["evaluation_criteria"],
    )

    try:
        response = litellm.completion(
            model="xai/grok-beta",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()

        # Try to extract JSON from response
        if content.startswith("["):
            trends = json.loads(content)
        else:
            # Try to find JSON array in response
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end > start:
                trends = json.loads(content[start:end])
            else:
                return None

        # Add focus_area to each trend
        for trend in trends:
            trend["focus_area"] = focus_area
            trend["timestamp"] = datetime.now(timezone.utc).isoformat()

        return trends

    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def run_full_analysis() -> dict:
    """
    Run analysis for all focus areas.

    Returns dict with radar_date and trends list.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    all_trends = []

    for focus_area in FOCUS_AREAS:
        trends = analyze_focus_area(focus_area)
        if trends:
            all_trends.extend(trends)

    return {
        "radar_date": today,
        "trends": all_trends,
    }
