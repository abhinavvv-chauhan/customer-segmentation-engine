import pandas as pd

from src.segmentation.profile import map_segments


def test_map_segments_totality():
    # Setup dummy clusters
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "recency": [10, 100, 200, 300],
            "frequency": [50, 10, 5, 1],
            "monetary_value": [1000, 500, 100, 10],
            "cluster": [0, 1, 2, 3],
        }
    )

    mapped_df = map_segments(df)

    # Assert every segment gets a name and action
    assert mapped_df["segment_name"].isnull().sum() == 0
    assert mapped_df["recommended_action"].isnull().sum() == 0
    assert len(mapped_df["segment_name"].unique()) == 4
