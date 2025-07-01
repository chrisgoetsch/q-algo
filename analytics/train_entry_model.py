# File: analytics/train_entry_model.py — patched for mesh_log.jsonl support

import os
import json
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

# Paths
CSV_PATH = "data/spy_0dte_merged_cleaned.csv"
JSONL_PATH = "logs/mesh_log.jsonl"
MODEL_SAVE_PATH = "core/models/entry_model.pkl"
FEATURE_PLOT_PATH = "logs/xgboost_feature_importance.png"

# Load training data

def load_from_jsonl(path=JSONL_PATH, auto_label=True, threshold=90):
    print(f"🔍 Loading from JSONL: {path}")
    rows = []
    with open(path, "r") as f:
        for line in f:
            try:
                j = json.loads(line)
                if "agent_signals" not in j:
                    continue
                row = {**j["agent_signals"]}
                row["mesh_score"] = j.get("mesh_score", 0)
                row["label"] = j.get("label")
                if auto_label:
                    row["label"] = 1 if row["mesh_score"] >= threshold else 0
                if row["label"] is not None:
                    rows.append(row)
            except Exception as e:
                print(f"⚠️ Skipping malformed row: {e}")
    df = pd.DataFrame(rows)
    print(f"✅ Loaded {len(df)} rows from mesh log")
    return df.drop(columns=["label"]), df["label"]

def load_from_csv():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Missing training file: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    if "label" not in df.columns:
        raise ValueError("Training set must include a 'label' column")
    return df.drop(columns=["label"]), df["label"]

def plot_feature_importance(model, feature_names):
    importance = model.feature_importances_
    sorted_idx = importance.argsort()[::-1]
    top_features = [feature_names[i] for i in sorted_idx]
    top_scores = importance[sorted_idx]

    plt.figure(figsize=(12, 6))
    plt.bar(top_features, top_scores, color="skyblue")
    plt.xticks(rotation=90)
    plt.title("XGBoost Feature Importance")
    plt.tight_layout()
    os.makedirs(os.path.dirname(FEATURE_PLOT_PATH), exist_ok=True)
    plt.savefig(FEATURE_PLOT_PATH)
    print(f"📊 Feature importance saved to {FEATURE_PLOT_PATH}")

def train_and_save_model(X, y):
    if len(y.unique()) < 2:
        print("❌ Only one class present. Cannot train.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print("\n🧠 Classification Report:")
    print(classification_report(y_test, preds))

    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"✅ Model saved to {MODEL_SAVE_PATH}")

    plot_feature_importance(model, list(X.columns))

if __name__ == "__main__":
    try:
        X, y = load_from_jsonl()
    except Exception as e:
        print(f"⚠️ Failed loading from JSONL: {e}. Falling back to CSV.")
        X, y = load_from_csv()

    train_and_save_model(X, y)
