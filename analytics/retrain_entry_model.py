# File: analytics/retrain_entry_model.py

import os
import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from joblib import dump

REINFORCEMENT_PATH = "assistants/reinforcement_profile.jsonl"
MODEL_OUTPUT_PATH = "core/models/entry_model.pkl"

FEATURE_COLS = [
    "price", "iv", "volume", "skew", "delta", "gamma", "dealer_flow",
    "mesh_confidence", "mesh_score", "alpha_decay",
    "agent_q_block", "agent_q_trap", "agent_q_quant", "agent_q_precision", "agent_q_scout"
]

# --- Load and preprocess data ---
def load_reinforcement_data():
    if not os.path.exists(REINFORCEMENT_PATH):
        print(f"❌ No reinforcement data found at {REINFORCEMENT_PATH}")
        return pd.DataFrame()

    data = []
    with open(REINFORCEMENT_PATH, "r") as f:
        for line in f:
            try:
                record = json.loads(line)
                data.append(record)
            except Exception as e:
                print(f"⚠️ Skipping malformed line: {e}")

    return pd.DataFrame(data)

# --- Feature engineering ---
def preprocess(df):
    df = df.copy()
    df = df.dropna(subset=["pnl"])
    df["label"] = (df["pnl"] > 0).astype(int)

    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0

    features = df[FEATURE_COLS]
    labels = df["label"]
    return features, labels

# --- Train model ---
def train_model(X, y):
    if len(X) < 2:
        print("⚠️ Not enough data to split for training. Train aborted.")
        return

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"✅ Model accuracy: {acc:.3f}")
    print(classification_report(y_test, y_pred))

    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    dump(model, MODEL_OUTPUT_PATH)
    print(f"📦 Model saved to {MODEL_OUTPUT_PATH}")

# --- Main flow ---
def main():
    df = load_reinforcement_data()
    if df.empty:
        print("⚠️ No valid data to train on.")
        return

    X, y = preprocess(df)
    train_model(X, y)

if __name__ == "__main__":
    main()