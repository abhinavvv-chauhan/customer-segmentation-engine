import pandas as pd


def map_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Map numeric clusters to descriptive names and actions based on their RFM profiles."""
    profile_df = df.copy()

    # Calculate means per cluster
    cluster_means = profile_df.groupby("cluster")[
        ["recency", "frequency", "monetary_value"]
    ].mean()

    if len(cluster_means) != 4:
        raise ValueError("Expected exactly 4 clusters for mapping.")

    # 1. Champions: highest monetary value
    champions_idx = cluster_means["monetary_value"].idxmax()
    
    # 2. Hibernating: lowest monetary value
    hibernating_idx = cluster_means["monetary_value"].idxmin()
    
    remaining = [idx for idx in cluster_means.index if idx not in (champions_idx, hibernating_idx)]
    
    # Between the remaining two, the one with lower recency (more recent) is "Promising"
    if cluster_means.loc[remaining[0], "recency"] < cluster_means.loc[remaining[1], "recency"]:
        promising_idx = remaining[0]
        at_risk_idx = remaining[1]
    else:
        promising_idx = remaining[1]
        at_risk_idx = remaining[0]

    segment_names = {
        champions_idx: "Champions",
        promising_idx: "Promising",
        at_risk_idx: "At-Risk High-Value",
        hibernating_idx: "Hibernating",
    }

    actions = {
        "Champions": "Reward them. Early adopters for new products.",
        "Promising": "Offer personalized recommendations to increase order frequency.",
        "At-Risk High-Value": "Send personalized emails to reconnect, offer renewals.",
        "Hibernating": "Offer standard discounts. Minimal marketing spend.",
    }

    profile_df["segment_name"] = profile_df["cluster"].map(segment_names)
    profile_df["recommended_action"] = profile_df["segment_name"].map(actions)

    return profile_df
