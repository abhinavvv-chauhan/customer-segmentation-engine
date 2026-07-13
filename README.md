# Customer Segmentation Engine

> **Business question:** "Which customer groups should we retain, grow, or win back — and what's the play for each?"

![Dashboard Screenshot](./docs/screenshot.png) *(Placeholder for deployed app screenshot)*

## Top Recommendations
1. **Champions**: Reward them with exclusive previews. They are your early adopters and most profitable cohort.
2. **At-Risk High-Value**: Immediately trigger personalized win-back emails with targeted discounts to prevent losing significant revenue share.
3. **Loyal Customers**: Create an upsell path to convert them into Champions and ask for reviews to boost brand equity.

---

## Architecture & Stack
- **Ingestion**: `dlt` (Declarative EL directly to DuckDB) + **Deterministic Synthetic Data Generator** (Simulates a live, continuously updating e-commerce database to cause real-time model drift)
- **Warehouse**: DuckDB (Local, fast analytical DB)
- **Transform**: `dbt-core` (SQL models, tests, and documentation)
- **Machine Learning**: `scikit-learn`, `pandas`, `pandera`
- **Application**: `Streamlit`
- **Orchestration**: GitHub Actions

## Setup & Running

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Ingest data to DuckDB**:
   ```bash
   uv run python ingestion/pipeline.py
   ```

3. **Build dbt models (RFM features)**:
   ```bash
   uv run dbt build --profiles-dir dbt --project-dir dbt
   ```

4. **Run Segmentation (K-Means)**:
   ```bash
   uv run python -m src.segmentation.main
   ```

5. **Start Streamlit App**:
   ```bash
   uv run streamlit run app/streamlit_app.py
   ```
