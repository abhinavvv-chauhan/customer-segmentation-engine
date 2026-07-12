import numpy as np
from sklearn.cluster import KMeans

from src.segmentation.config import N_CLUSTERS, RANDOM_STATE


def fit_kmeans(X: np.ndarray, n_clusters: int = N_CLUSTERS) -> np.ndarray:
    """Fit K-Means clustering and return cluster labels."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    kmeans.fit(X)
    return kmeans.labels_
