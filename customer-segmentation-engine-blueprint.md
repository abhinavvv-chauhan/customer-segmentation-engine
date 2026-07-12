# Customer Segmentation Engine (RFM + Clustering) — Project Blueprint

> **Analyst signal:** turning behavior into *actionable* segments marketing can target.
>
> **Business question:** "Which customer groups should we retain, grow, or win back — and what's the play for each?"

A capstone-worthy, SaaS-level data science project for analyst roles. This blueprint covers the free tech stack, repository structure, and the up-to-date (2026) standards that make it read as a shipped product rather than a notebook.

---

## Free tech stack (2026-current)

| Layer | Choice | Why |
|---|---|---|
| **Language** | Python 3.12+ | Current stable; 3.13 fine too |
| **Env / packaging** | **uv** + `pyproject.toml` | Replaced pip/poetry as the default — 10–100× faster, lockfile built in |
| **Ingestion** | **dlt** (`dlthub`) | Declarative EL, schema evolution, loads straight into DuckDB |
| **Warehouse** | **DuckDB** (local) or **MotherDuck** free tier (hosted) | Crushes single-node analytics; zero infra |
| **Transform** | **dbt-core** + `dbt-duckdb` | RFM feature marts with tests + docs |
| **DS core** | **scikit-learn**, **scipy**, `yellowbrick` (optional) | K-means/hierarchical, silhouette, scaling |
| **Data validation** | **Pandera** (dataframe schemas) + dbt tests | Runtime + warehouse-level checks |
| **App** | **Streamlit** (deploy to Streamlit Community Cloud) | Free hosted interactive app |
| **Orchestration** | **GitHub Actions cron** (start here) or **Dagster** | Scheduled refresh proves it's a system |
| **CI** | **GitHub Actions** | Runs lint + tests + `dbt build` on every PR |
| **Lint/format** | **Ruff** (lint + format, replaces black/isort/flake8) | Single fast tool, current standard |
| **Testing** | **pytest** | Unit-test the RFM/scoring logic |
| **Types** | **ty** (Astral) or **mypy** | Optional but a strong signal |
| **Pre-commit** | **pre-commit** hooks (ruff, dbt parse) | Keeps the repo clean |

You don't need a paid tier for any of it. DuckDB + Streamlit Cloud + GitHub Actions covers warehouse, hosting, and scheduling for $0.

---

## Project structure

```
customer-segmentation-engine/
├── README.md                      # business question + screenshot + recommendation UP TOP
├── pyproject.toml                 # uv-managed deps, ruff/pytest config
├── uv.lock                        # committed lockfile
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       ├── ci.yml                 # ruff + pytest + dbt build on every PR
│       └── refresh.yml            # scheduled cron: run pipeline, redeploy data
│
├── ingestion/
│   └── pipeline.py                # dlt: raw source → DuckDB (raw schema)
│
├── warehouse/
│   └── retail.duckdb              # gitignored; built by pipeline (or MotherDuck)
│
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml               # duckdb target
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_orders.sql
│   │   │   ├── stg_customers.sql
│   │   │   └── _staging.yml        # tests + docs (not_null, unique)
│   │   ├── intermediate/
│   │   │   └── int_order_lines_cleaned.sql   # dedupe, cancellations, returns
│   │   └── marts/
│   │       ├── fct_rfm.sql          # one row per customer: R, F, M + scores
│   │       ├── dim_customers.sql
│   │       └── _marts.yml           # schema tests + column descriptions
│   └── seeds/                       # small reference data if needed
│
├── src/
│   └── segmentation/
│       ├── __init__.py
│       ├── config.py               # paths, params (k range, random_state)
│       ├── rfm.py                   # RFM computation + quantile scoring
│       ├── features.py              # scaling, skew handling (log/Box-Cox)
│       ├── cluster.py               # fit K-means/hierarchical, choose k
│       ├── evaluate.py              # silhouette, elbow, Davies-Bouldin
│       ├── profile.py               # segment naming + action mapping
│       └── io.py                    # read from DuckDB, write segments back
│
├── tests/
│   ├── test_rfm.py                 # known-input → known-score assertions
│   ├── test_cluster.py             # determinism (fixed seed), shape checks
│   └── test_profile.py             # segment→action mapping is total
│
├── app/
│   ├── streamlit_app.py            # the deployed interactive app
│   └── components/                 # charts, segment cards, filters
│
├── analysis/
│   ├── 01_eda.ipynb                # exploration (kept, but not the product)
│   ├── 02_k_selection.ipynb        # elbow/silhouette evidence
│   └── methodology.md              # how you chose k, scaling, naming logic
│
└── data/
    └── raw/                        # gitignored; source CSV if not via API
```

**The structure encodes the story:** ingest (`ingestion/`) → warehouse (`warehouse/`) → transform (`dbt/`) → model (`src/segmentation/`) → serve (`app/`) → explain (`analysis/`). A reviewer can trace the whole pipeline from the tree alone.

---

## The critical design decision: split RFM (SQL) from clustering (Python)

This is what separates a strong version from a naive one:

- **RFM belongs in dbt** (`fct_rfm.sql`) — recency, frequency, monetary are deterministic SQL aggregations. Doing them as tested, documented marts shows analytics-engineering maturity.
- **Clustering belongs in `src/`** — scaling, k-selection, and fitting are stochastic and need pytest + a fixed `random_state`. The `cluster.py` step reads `fct_rfm`, fits, and writes a `customer_segments` table back to DuckDB, which the app and dbt can both consume.

Naive portfolios do everything in one notebook. Splitting deterministic-SQL from stochastic-Python is the signal.

---

## Up-to-date standards to hit (the "SaaS-level" checklist)

**DS rigor (the part most portfolios skip):**
- **Scale before clustering** — K-means is distance-based; standardize, and **handle RFM's heavy skew** (log or Box-Cox on Monetary/Frequency) before scaling. Call this out explicitly.
- **Justify *k*** with *two* methods that agree — elbow (inertia) **and** silhouette; mention Davies-Bouldin as a tiebreaker. Show the plots in `analysis/`.
- **Fix `random_state`** everywhere so results are reproducible (and testable).
- **Name every segment** ("Champions", "At-Risk High-Value", "Hibernating") and map each to **one recommended action** — the mapping should be *total* (every segment has a play), enforced by a test.
- Consider showing you know the alternatives: a sentence on why K-means over DBSCAN/GMM here, and a nod to the classic **RFM quantile scoring** as a transparent baseline you compare clustering against.

**Engineering standards:**
- **uv + lockfile** committed; anyone can `uv sync` and reproduce exactly.
- **Ruff** for lint+format, **pytest** green, **dbt tests** green — all enforced in CI.
- **Scheduled refresh** (GH Actions cron) so the deployed app's data is fresh — this is what makes it "a system."
- **Pandera schema** on the dataframe entering the clustering step (fail loud on bad input).
- **Secrets** via GitHub Actions secrets / Streamlit secrets, never committed.

**Product/analyst standards:**
- README leads with the **business question, a screenshot of the live app, and the top-3 recommendations** — before any setup instructions.
- The Streamlit app lets you **filter to a segment and see size, revenue share, avg RFM, and the recommended play** — plus a "what % of revenue is at risk" headline metric.

---

## Suggested build order

1. `uv init`, add deps, set up ruff + pytest + pre-commit, empty CI.
2. `dlt` pipeline: land the raw retail data in DuckDB.
3. dbt staging + `int_order_lines_cleaned` (dedupe, drop cancellations/returns — the Online Retail dataset needs this).
4. `fct_rfm` mart + schema tests.
5. `src/segmentation`: RFM scoring → scaling → k-selection → fit → write `customer_segments`. Unit-test as you go.
6. `analysis/` notebooks to document k-selection + methodology.
7. Streamlit app reading `customer_segments`; deploy to Streamlit Cloud.
8. GH Actions cron for scheduled refresh; polish README with screenshot + recommendations.

---

## Data note

If you use **UCI Online Retail** (the most common choice): it needs real cleaning — cancellations (InvoiceNo starting `C`), negative/zero quantities, missing CustomerID, and it's UK-centric. Handling that in `int_order_lines_cleaned` with documented dbt tests is itself a strong analyst signal, so lean into it rather than hiding it.

**Alternative free datasets:** Instacart Market Basket, Brazilian Olist E-commerce.
