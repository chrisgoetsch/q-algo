# File: analytics/qthink_cluster_analysis.py

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from openai import OpenAI
from core.logger_setup import logger

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

client = OpenAI(api_key=OPENAI_API_KEY)

DECAY_LOG_PATH = "logs/alpha_decay_log.jsonl"

def load_decay_log():
    if not os.path.exists(DECAY_LOG_PATH):
        logger.warning(f"❌ No decay log found at {DECAY_LOG_PATH}")
        return pd.DataFrame()

    entries = []
    with open(DECAY_LOG_PATH, "r") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                entries.append(data)
            except Exception as e:
                logger.warning(f"⚠️ Skipping malformed line: {e}")
    return pd.DataFrame(entries)

def query_gpt_for_exit_policy(df):
    try:
        sample_data = df[["alpha_decay", "pnl"]].round(4).dropna().to_dict(orient="records")
        sample_text = json.dumps(sample_data[:20], indent=2)

        prompt = (
            "You are a trading strategy expert. Below is data from a 0DTE options trading model. "
            "Each record shows alpha_decay (a value from 0 to 1 representing signal deterioration over time) "
            "and pnl (profit or loss). Analyze the patterns and recommend an ideal alpha_decay exit threshold. "
            "Should we exit at 0.4? 0.6? 0.8? Use statistical logic or pattern detection.\n\n"
            f"Sample data:\n{sample_text}\n\n"
            "Respond with a single paragraph of reasoning and your recommended decay threshold."
        )

        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        reply = response.choices[0].message.content
        logger.info(f"\n🤖 GPT-4o Reasoning:\n{reply}")

        log_gpt_exit_recommendation(reply)
        return reply

    except Exception as e:
        logger.error(f"⚠️ GPT analysis failed: {e}")
        return None

def cluster_and_plot(df):
    if df.empty:
        logger.warning("⚠️ No data to plot.")
        return

    df["bucket"] = pd.cut(df["alpha_decay"], bins=[0, 0.3, 0.5, 0.7, 1.0], labels=["low", "moderate", "high", "critical"])
    grouped = df.groupby("bucket")["pnl"].agg(["count", "mean", "median", "min", "max"]).reset_index()

    logger.info("\n📊 PnL by Alpha Decay Bucket:\n" + grouped.to_string(index=False))

    plt.figure(figsize=(8, 5))
    plt.boxplot([df[df["bucket"] == b]["pnl"] for b in df["bucket"].unique()], labels=df["bucket"].unique())
    plt.title("PnL Distribution by Alpha Decay Bucket")
    plt.xlabel("Alpha Decay Level")
    plt.ylabel("PnL")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def suggest_exit_threshold(df):
    if df.empty:
        return None

    df_sorted = df.sort_values("alpha_decay")
    rolling = df_sorted["pnl"].rolling(window=10).median()

    for i, val in enumerate(rolling):
        if val is not None and val < 0:
            decay_trigger = df_sorted.iloc[i]["alpha_decay"]
            logger.info(f"\n🚨 Suggested Exit Threshold: alpha_decay ≈ {round(decay_trigger, 3)} (median PnL turned negative)")
            return decay_trigger

    logger.info("\n✅ No strong decay threshold found. Median PnL stayed positive.")
    return None

def run_cluster_analysis():
    logger.info("🔍 QThink Cluster Analysis: Alpha Decay vs. Trade Outcome")
    df = load_decay_log()

    if df.empty:
        return

    df["alpha_decay"] = pd.to_numeric(df["alpha_decay"], errors="coerce")
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["alpha_decay", "pnl"])

    cluster_and_plot(df)
    suggest_exit_threshold(df)
    query_gpt_for_exit_policy(df)

def log_gpt_exit_recommendation(reply: str):
    log_path = "logs/qthink_journal_summary.json"
    profile_path = "training_data/reinforcement_profile.json"
    today = datetime.utcnow().strftime("%Y-%m-%d")

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "exit_threshold_analysis",
        "date": today,
        "model": GPT_MODEL,
        "summary": reply
    }

    try:
        # Append to insights log
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(entry)

        with open(log_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"📝 GPT output saved to {log_path}")
    except Exception as e:
        logger.error(f"⚠️ Failed to write GPT journal: {e}")

    # 🔁 Update reinforcement profile with decay threshold if possible
    try:
        if "0." in reply:
            import re
            matches = re.findall(r"0\.\d+", reply)
            thresholds = [float(x) for x in matches if 0.0 < float(x) < 1.0]
            suggested = min(thresholds, key=lambda x: abs(x - 0.6)) if thresholds else None
        else:
            suggested = None

        if suggested:
            if os.path.exists(profile_path):
                with open(profile_path, "r") as f:
                    profile = json.load(f)
            else:
                profile = {}

            profile["suggested_exit_decay"] = round(suggested, 3)
            with open(profile_path, "w") as f:
                json.dump(profile, f, indent=2)

            logger.info(f"🧠 Reinforcement profile updated with suggested_exit_decay: {suggested:.3f}")
        else:
            logger.warning("⚠️ No numeric threshold extracted from GPT reply.")
    except Exception as e:
        logger.error(f"⚠️ Failed to update reinforcement profile: {e}")

def analyze_trade_with_gpt(entry_data, exit_data):
    """
    Use GPT to generate feedback on a trade's entry and exit.
    """
    import openai
    import os

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("GPT_MODEL", "gpt-4o")

    prompt = f"""
You are a trading analyst. Evaluate the following SPY 0DTE trade:

Entry Time: {entry_data['timestamp']}
Entry Price: {entry_data['price']}
Exit Time: {exit_data['timestamp']}
Exit Price: {exit_data['exit_price']}
PnL: {exit_data['pnl_percentage']:.2f}%
Exit Reason: {exit_data['exit_reason']}

Was this a good trade? Briefly explain strengths, weaknesses, and potential improvements.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return {
            "feedback": response.choices[0].message.content.strip(),
            "model": model,
            "pnl": exit_data['pnl_percentage'],
            "regret_tag": "low" if exit_data["pnl_percentage"] > 0 else "high"
        }
    except Exception as e:
        return {"error": str(e)}

