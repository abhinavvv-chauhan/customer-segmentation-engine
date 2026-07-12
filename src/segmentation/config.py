from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
WAREHOUSE_DIR = BASE_DIR / "warehouse"
DB_PATH = WAREHOUSE_DIR / "retail.duckdb"

# Clustering Parameters
RANDOM_STATE = 42
N_CLUSTERS = 4
