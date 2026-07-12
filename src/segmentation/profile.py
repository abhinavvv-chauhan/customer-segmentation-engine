import pandas as pd


def map_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Map numeric clusters to descriptive names and actions based on their RFM profiles."""
    profile_df = df.copy()

    # Calculate means per cluster
    cluster_means = profile_df.groupby("cluster")[
        ["recency", "frequency", "monetary_value"]
    ].mean()

    # Dynamic assignment based on ranks
    # Lower recency is better (rank ascending), Higher frequency/monetary is better (rank descending)
    cluster_means["r_rank"] = cluster_means["recency"].rank(ascending=True)
    cluster_means["f_rank"] = cluster_means["frequency"].rank(ascending=False)
    cluster_means["m_rank"] = cluster_means["monetary_value"].rank(ascending=False)

    cluster_means["score"] = (
        cluster_means["r_rank"] + cluster_means["f_rank"] + cluster_means["m_rank"]
    )

    # Sort by overall score (lower score = better ranks overall)
    sorted_clusters = cluster_means.sort_values("score").index.tolist()

    # Ensure we handle exactly 4 clusters (as configured)
    if len(sorted_clusters) != 4:
        raise ValueError("Expected exactly 4 clusters for mapping.")

    segment_names = {
        sorted_clusters[0]: "Champions",
        sorted_clusters[1]: "Loyal Customers",
        sorted_clusters[2]: "At-Risk High-Value",
        sorted_clusters[3]: "Hibernating",
    }

    actions = {
        "Champions": "Reward them. Early adopters for new products.",
        "Loyal Customers": "Upsell higher value products. Ask for reviews.",
        "At-Risk High-Value": "Send personalized emails to reconnect, offer renewals.",
        "Hibernating": "Offer standard discounts. Minimal marketing spend.",
    }

    profile_df["segment_name"] = profile_df["cluster"].map(segment_names)
    profile_df["recommended_action"] = profile_df["segment_name"].map(actions)

    return profile_df
