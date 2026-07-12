import duckdb
import pandas as pd
import pandera.pandas as pa

from src.segmentation.config import DB_PATH

# Pandera schema for input validation
rfm_schema = pa.DataFrameSchema(
    {
        "customer_id": pa.Column(int, nullable=False, coerce=True),
        "recency": pa.Column(int, pa.Check.ge(0), coerce=True),
        "frequency": pa.Column(int, pa.Check.gt(0), coerce=True),
        "monetary_value": pa.Column(float, coerce=True),
    }
)


def load_rfm_data() -> pd.DataFrame:
    """Load RFM features from duckdb warehouse."""
    with duckdb.connect(str(DB_PATH)) as con:
        df = con.execute("SELECT * FROM fct_rfm").df()

    # Fail loud if schema is violated
    return rfm_schema.validate(df)


def save_segments(df: pd.DataFrame) -> None:
    """Save customer segments back to DuckDB and as a Parquet file for Streamlit."""
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("CREATE OR REPLACE TABLE customer_segments AS SELECT * FROM df")
    
    # Save as parquet to avoid duckdb out-of-memory segfaults in Streamlit Cloud
    parquet_path = DB_PATH.parent / "customer_segments.parquet"
    df.to_parquet(parquet_path, index=False)
