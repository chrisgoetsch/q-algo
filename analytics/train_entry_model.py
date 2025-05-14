# File: analytics/train_entry_model.py

import os
import json
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

SCORE_LOG_PATH = os.getenv("SCORE_LOG_PATH", "logs/qthink_score_breakdown.jsonl")
MODEL_SAVE_PATH = "core/models/entry_model.pkl"
FEATURE_PLOT_PATH = os.getenv("FEATURE_PLOT_PATH", "logs/xgboost_feature_importance.png")

LABEL_KEYWORDS = ["profit", "target", "strong", "alignment"]
NEGATIVE_KEYWORDS = ["bad entry", "mesh conflict", "regret"]


def load_scored_data():
    if not os.path.exists(SCORE_LOG_PATH):
        raise FileNotFoundError(f"{SCORE_LOG_PATH} not found")

    rows = []
    with open(SCORE_LOG_PATH, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                label_text = entry.get("rationale", "").lower()
                is_good = any(k in label_text for k in LABEL_KEYWORDS)
                is_bad = any(k in label_text for k in NEGATIVE_KEYWORDS)
                if not (is_good or is_bad):
                    continue
                label = 1 if is_good else 0
                row = entry.get("features", {})
                row["label"] = label
                rows.append(row)
            except Exception:
                continue

    return pd.DataFrame(rows)


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
    plt.savefig(FEATURE_PLOT_PATH)
    print(f"📊 Feature importance plot saved to {FEATURE_PLOT_PATH}")


def train_and_save_model(df):
    X = df.drop("label", axis=1)
    y = df["label"]

    if y.nunique() < 2:
        print("❌ Error: Only one class present in dataset. Need at least one positive and one negative example.")
        return

    if len(df) < 4:
        print("⚠️ Small dataset — training on full data without test split.")
        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        model.fit(X, y)
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        print(classification_report(y_test, preds))

    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"✅ Model saved to {MODEL_SAVE_PATH}")

    plot_feature_importance(model, list(X.columns))


if __name__ == "__main__":
    df = load_scored_data()
    if df.empty:
        print("⚠️ No labeled score data found in qthink_score_breakdown.jsonl")
    else:
        print(df["label"].value_counts())
        train_and_save_model(df)
