import os
import urllib.request
from pathlib import Path

import dlt
import pandas as pd


def download_data(url: str, dest_path: str) -> None:
    """Download the dataset if it doesn't exist."""
    if not os.path.exists(dest_path):
        print(f"Downloading data from {url}...")
        urllib.request.urlretrieve(url, dest_path)
        print("Download complete.")
    else:
        print("Data already exists. Skipping download.")


@dlt.resource(name="raw_orders", write_disposition="replace")
def online_retail_source(file_path: str):
    """Read the Excel file and yield chunks."""
    # Read Excel using pandas
    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path)

    # Yield the whole dataframe (or could yield in chunks)
    yield df.to_dict(orient="records")


def run_pipeline():
    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)

    file_path = data_dir / "online_retail.xlsx"
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"

    # 1. Download data
    download_data(url, str(file_path))

    # 2. Configure dlt pipeline
    # The duckdb file will be created in the warehouse directory
    warehouse_dir = base_dir / "warehouse"
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    duckdb_path = warehouse_dir / "retail.duckdb"

    pipeline = dlt.pipeline(
        pipeline_name="retail_pipeline",
        destination=dlt.destinations.duckdb(credentials=str(duckdb_path)),
        dataset_name="raw",
    )

    # 3. Run pipeline
    print("Running dlt pipeline to load data into DuckDB...")
    load_info = pipeline.run(online_retail_source(str(file_path)))
    print(load_info)


if __name__ == "__main__":
    run_pipeline()
