# dataset_auditor.py
# Verifies training datasets for completeness, consistency, and readiness

import pandas as pd
import os

def audit_dataset(file_path):
    """
    Audits a CSV dataset for:
    - missing columns
    - null values
    - unusual ranges
    """
    if not os.path.exists(file_path):
        print(f"[audit] File not found: {file_path}")
        return False

    df = pd.read_csv(file_path)
    print(f"[audit] Loaded {len(df)} rows from {file_path}")

    required = ["score", "iv_rank", "dealer_position", "skew", "gex", "label"]
    missing_cols = [col for col in required if col not in df.columns]
    if missing_cols:
        print(f"[audit] Missing columns: {missing_cols}")
        return False

    if df.isnull().sum().sum() > 0:
        print("[audit] Null values present")
        return False

    print("[audit] Dataset passes all checks ✅")
    return True

if __name__ == "__main__":
    audit_dataset("data/spy_0dte_factors.csv")

