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


import datetime
import random
from typing import List, Dict

def generate_synthetic_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Shifts the base dataset to end 30 days ago, then deterministically generates 
    new transactions up to the current date to simulate a live, drifting dataset.
    """
    print("Generating deterministic synthetic transactions...")
    
    # 1. Shift base data
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    original_max_date = df["InvoiceDate"].max()
    
    # Target anchor date for the end of the base dataset: 30 days ago
    target_anchor_date = datetime.datetime.now() - datetime.timedelta(days=30)
    time_shift = target_anchor_date - original_max_date
    df["InvoiceDate"] = df["InvoiceDate"] + time_shift
    
    # 2. Get unique customers and products to sample from
    customers = df["CustomerID"].dropna().unique().tolist()
    product_sample = df[["StockCode", "Description", "UnitPrice"]].dropna().drop_duplicates(subset=["StockCode"]).head(100).to_dict('records')
    
    # 3. Generate the bridge (from 29 days ago up to today)
    new_rows: List[Dict] = []
    for i in range(29, -1, -1):
        sim_date = datetime.datetime.now() - datetime.timedelta(days=i)
        
        # Seed random generator with the date for determinism
        seed_val = int(sim_date.strftime("%Y%m%d"))
        random.seed(seed_val)
        
        num_transactions = random.randint(20, 80)
        for _ in range(num_transactions):
            customer = random.choice(customers)
            product = random.choice(product_sample)
            qty = random.randint(1, 15)
            invoice_no = f"SIM{seed_val}{random.randint(1000, 9999)}"
            
            new_rows.append({
                "InvoiceNo": invoice_no,
                "StockCode": product["StockCode"],
                "Description": product["Description"],
                "Quantity": qty,
                "InvoiceDate": sim_date,
                "UnitPrice": product["UnitPrice"],
                "CustomerID": customer,
                "Country": "United Kingdom"
            })
            
    if new_rows:
        synthetic_df = pd.DataFrame(new_rows)
        df = pd.concat([df, synthetic_df], ignore_index=True)
        
    print(f"Added {len(new_rows)} synthetic transactions over the last 30 days.")
    return df

@dlt.resource(name="raw_orders", write_disposition="replace")
def online_retail_source(file_path: str):
    """Read the Excel file, generate synthetic drift, and yield chunks."""
    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path)
    
    # Generate live synthetic data to age base customers and migrate segments naturally
    df = generate_synthetic_transactions(df)

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
