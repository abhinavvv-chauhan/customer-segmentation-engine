from src.segmentation.cluster import fit_kmeans
from src.segmentation.features import handle_skew, scale_features
from src.segmentation.io import load_rfm_data, save_segments
from src.segmentation.profile import map_segments


def run_segmentation():
    print("Loading RFM data from DuckDB...")
    df = load_rfm_data()

    print("Transforming features...")
    df_transformed = handle_skew(df)
    X_scaled, scaler = scale_features(df_transformed)

    print("Fitting K-Means clustering...")
    df["cluster"] = fit_kmeans(X_scaled)

    print("Profiling and mapping segments...")
    df_profiled = map_segments(df)

    print("Saving segments back to DuckDB...")
    save_segments(df_profiled)

    print("Segmentation complete!")


if __name__ == "__main__":
    run_segmentation()
