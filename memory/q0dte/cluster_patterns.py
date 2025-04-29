# cluster_patterns.py
# Builds a clustering model from GPT-labeled trade pattern tags

import pandas as pd
import json
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
from pathlib import Path

LABELS_PATH = Path("memory/qthink/labeled_trades.jsonl")
OUTPUT_PATH = Path("memory/q0dte/pattern_cluster.pkl")


def load_tags_from_jsonl(n=100):
    if not LABELS_PATH.exists():
        return []
    with open(LABELS_PATH, "r") as f:
        lines = f.readlines()[-n:]
        entries = [json.loads(l) for l in lines]
    tag_strings = [" ".join(entry.get("tags", [])) for entry in entries if 
entry.get("tags")]
    return tag_strings


def build_cluster_model(tag_strings: list, n_clusters=4):
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(tag_strings)
    model = KMeans(n_clusters=n_clusters, random_state=42)
    model.fit(X)
    return model, vectorizer


def save_model(model, vectorizer):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump((model, vectorizer), OUTPUT_PATH)
    print(f"✅ Saved pattern cluster model to {OUTPUT_PATH}")


if __name__ == "__main__":
    tags = load_tags_from_jsonl(n=100)
    if not tags:
        print("❌ No tags found to cluster.")
    else:
        model, vectorizer = build_cluster_model(tags)
        save_model(model, vectorizer)

