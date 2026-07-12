import numpy as np
import pandas as pd

from src.segmentation.features import handle_skew


def test_handle_skew():
    """Test that log1p is applied correctly to handle skew."""
    df = pd.DataFrame(
        {"recency": [0, 10], "frequency": [1, 10], "monetary_value": [10.0, 100.0]}
    )

    transformed = handle_skew(df)

    # Check that log1p was applied
    np.testing.assert_allclose(transformed["recency_log"], np.log1p(df["recency"]))
    np.testing.assert_allclose(transformed["frequency_log"], np.log1p(df["frequency"]))
    np.testing.assert_allclose(
        transformed["monetary_log"], np.log1p(df["monetary_value"])
    )
