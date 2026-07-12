import numpy as np

from src.segmentation.cluster import fit_kmeans
from src.segmentation.config import N_CLUSTERS


def test_kmeans_determinism():
    """Test that K-means produces deterministic outputs for the same seed."""
    X = np.array(
        [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [10.0, 10.0, 10.0], [20.0, 20.0, 20.0]]
    )
    labels_1 = fit_kmeans(X, n_clusters=2)
    labels_2 = fit_kmeans(X, n_clusters=2)

    np.testing.assert_array_equal(labels_1, labels_2)


def test_kmeans_shape():
    """Test that K-means outputs correct number of labels."""
    X = np.random.rand(10, 3)
    labels = fit_kmeans(X, n_clusters=N_CLUSTERS)
    assert len(labels) == 10
    assert len(np.unique(labels)) <= N_CLUSTERS
