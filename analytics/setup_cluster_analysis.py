# analytics/setup_cluster_analysis.py

import pandas as pd
import logging
from sklearn.cluster import KMeans

def load_data(file_path):
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logging.error(f"Failed to load data: {str(e)}", exc_info=True)
        return None

def run_clustering(data, n_clusters=5):
    try:
        if data is None:
            logging.warning("No data available for clustering.")
            return None

        model = KMeans(n_clusters=n_clusters, random_state=42)
        model.fit(data)
        labels = model.labels_
        logging.info(f"Clustering complete with {n_clusters} clusters.")
        return labels

    except Exception as e:
        logging.error(f"Clustering error: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="data/spy_features.csv", help="Input CSV for clustering")
    parser.add_argument("--clusters", type=int, default=5, help="Number of clusters")
    args = parser.parse_args()

    data = load_data(args.file)
    run_clustering(data, n_clusters=args.clusters)

