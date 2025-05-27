# File: qthink/qthink_pattern_matcher.py
# Purpose: GPT-style reasoning engine for reflecting on 0DTE pattern outcomes
# Used by q_0dte_brain.py to analyze memory and provide strategy feedback

from collections import defaultdict

def gpt_reflect_on_patterns(summary: dict) -> dict:
    """
    Accepts a summary of recent 0DTE pattern outcomes.
    Returns GPT-style feedback with:
    - Win rate
    - Pattern performance tags
    - Recommendations for each pattern
    """
    
    pattern_stats = defaultdict(lambda: {"count": 0, "wins": 0, "losses": 0})
    
    tags = summary.get("tags", [])
    results = summary.get("result_outcomes", [])

    # Build pattern statistics
    for tag, result in zip(tags, results):
        pattern_stats[tag]["count"] += 1
        if result == "win":
            pattern_stats[tag]["wins"] += 1
        elif result == "loss":
            pattern_stats[tag]["losses"] += 1

    # Generate GPT-like reflections
    reflections = {}
    for tag, stats in pattern_stats.items():
        count = stats["count"]
        wins = stats["wins"]
        losses = stats["losses"]
        win_rate = wins / count if count > 0 else 0.0

        reflection = {
            "win_rate": round(win_rate, 2),
            "trades_analyzed": count,
            "note": "",
            "action": ""
        }

        # GPT-style logic for actionable intelligence
        if win_rate >= 0.7 and count >= 5:
            reflection["note"] = "high-performing pattern"
            reflection["action"] = "reinforce"
        elif win_rate <= 0.4 and count >= 5:
            reflection["note"] = "underperforming"
            reflection["action"] = "review or disable"
        else:
            reflection["note"] = "inconclusive"
            reflection["action"] = "monitor"

        reflections[tag] = reflection

    return reflections
