import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def handle_skew(df: pd.DataFrame) -> pd.DataFrame:
    """Apply log transformation to handle heavy skew in RFM."""
    df_transformed = df.copy()

    # Log1p handles zeros safely
    df_transformed["recency_log"] = np.log1p(df["recency"])
    df_transformed["frequency_log"] = np.log1p(df["frequency"])
    df_transformed["monetary_log"] = np.log1p(df["monetary_value"])

    return df_transformed


def scale_features(df: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    """Standardize features for K-means."""
    features = ["recency_log", "frequency_log", "monetary_log"]
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df[features])
    return scaled_data, scaler
