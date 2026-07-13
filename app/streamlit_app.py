import streamlit as st
import streamlit.components.v1 as components
import duckdb
import json
from pathlib import Path

import datetime
# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "warehouse" / "retail.duckdb"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SegmentIQ · Customer Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide all Streamlit UI and fix double scrollbars
st.markdown(
    """<style>
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stAppDeployButton"],
.stAppDeployButton,.block-container{padding:0!important;max-width:100%!important;}
[data-testid="stVerticalBlock"]{gap:0!important;}
body { overflow: hidden !important; }
iframe { height: 100vh !important; border: none !important; }
</style>""",
    unsafe_allow_html=True,
)

import pandas as pd

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    parquet_path = BASE_DIR / "warehouse" / "customer_segments.parquet"
    return pd.read_parquet(parquet_path)

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# ── Pre-compute data for the frontend ────────────────────────────────────────
total_customers = int(len(df))
total_revenue = float(df["monetary_value"].sum())

segments_order = ["Champions", "Promising", "At-Risk High-Value", "Hibernating"]
seg_data = []
for seg_name in segments_order:
    seg_df = df[df["segment_name"] == seg_name]
    seg_data.append({
        "name": seg_name,
        "count": int(len(seg_df)),
        "pct": round(len(seg_df) / total_customers * 100, 1) if total_customers else 0,
        "revenue": round(float(seg_df["monetary_value"].sum()), 2),
        "rev_pct": round(float(seg_df["monetary_value"].sum()) / total_revenue * 100, 1) if total_revenue else 0,
        "avg_recency": round(float(seg_df["recency"].mean()), 1) if len(seg_df) else 0,
        "avg_frequency": round(float(seg_df["frequency"].mean()), 1) if len(seg_df) else 0,
        "avg_monetary": round(float(seg_df["monetary_value"].mean()), 2) if len(seg_df) else 0,
        "action": str(seg_df["recommended_action"].iloc[0]) if len(seg_df) else "",
    })

at_risk_revenue = float(df[df["segment_name"] == "At-Risk High-Value"]["monetary_value"].sum())
at_risk_pct = round(at_risk_revenue / total_revenue * 100, 1) if total_revenue else 0

# Sample for scatter plot
sample = df.sample(min(400, len(df)), random_state=42)
scatter_points = []
color_map_js = {"Champions": 0, "Promising": 1, "At-Risk High-Value": 2, "Hibernating": 3}
for _, row in sample.iterrows():
    scatter_points.append({
        "x": int(row["recency"]),
        "y": round(float(row["monetary_value"]), 2),
        "r": max(3, min(12, int(row["frequency"]) * 2)),
        "seg": color_map_js.get(row["segment_name"], 0),
    })

# Top customers per segment for the table
table_rows = []
for seg_name in segments_order:
    seg_df = df[df["segment_name"] == seg_name].nlargest(12, "monetary_value")
    for _, row in seg_df.iterrows():
        table_rows.append({
            "id": int(row["customer_id"]),
            "r": int(row["recency"]),
            "f": int(row["frequency"]),
            "m": round(float(row["monetary_value"]), 2),
            "seg": str(row["segment_name"]),
        })

dashboard_data = json.dumps({
    "total_customers": total_customers,
    "total_revenue": total_revenue,
    "at_risk_revenue": at_risk_revenue,
    "at_risk_pct": at_risk_pct,
    "segments": seg_data,
    "scatter": scatter_points,
    "table": table_rows,
})

# ── The complete HTML dashboard ──────────────────────────────────────────────
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/vanilla-tilt@1.8.1/dist/vanilla-tilt.min.js"></script>
<style>
/* ═══════════════════════════════════════════════════════════════════════════
   DESIGN SYSTEM
   ═══════════════════════════════════════════════════════════════════════════ */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}

:root {{
  --bg:         #06060f;
  --bg-card:    rgba(255,255,255,0.03);
  --bg-hover:   rgba(255,255,255,0.06);
  --border:     rgba(255,255,255,0.06);
  --glow:       rgba(99,102,241,0.35);
  --indigo:     #6366f1; --indigo-light: #a5b4fc;
  --cyan:       #06b6d4; --cyan-light:   #67e8f9;
  --amber:      #f59e0b; --amber-light:  #fcd34d;
  --slate:      #64748b; --slate-light:  #94a3b8;
  --red:        #ef4444;
  --text:       #f1f5f9;
  --text-2:     #94a3b8;
  --text-3:     #475569;
  --mono:       'JetBrains Mono', monospace;
  --sans:       'Inter', -apple-system, sans-serif;
  --radius:     16px;
  --ease:       cubic-bezier(0.22,1,0.36,1);
}}

html {{
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: var(--indigo) var(--bg);
}}
::-webkit-scrollbar {{ width:5px; }}
::-webkit-scrollbar-track {{ background:var(--bg); }}
::-webkit-scrollbar-thumb {{ background:var(--indigo); border-radius:3px; }}

body {{
  font-family: var(--sans);
  background: var(--bg);
  color: var(--text);
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}}

/* ── Animated Mesh Gradient BG ── */
.mesh-bg {{
  position:fixed; inset:0; z-index:0; pointer-events:none;
  background:
    radial-gradient(ellipse 70% 50% at 15% -5%,  rgba(99,102,241,0.13) 0%, transparent 55%),
    radial-gradient(ellipse 50% 35% at 85% 100%, rgba(6,182,212,0.10) 0%, transparent 50%),
    radial-gradient(ellipse 40% 40% at 50% 50%,  rgba(139,92,246,0.05) 0%, transparent 60%),
    var(--bg);
}}

/* ── Particle Canvas ── */
#particles {{ position:fixed; inset:0; z-index:0; }}

/* ── Layout ── */
.app {{ position:relative; z-index:1; max-width:1360px; margin:0 auto; padding:0 32px 64px; }}

/* ── Custom Cursor ── */
.cursor-dot {{
  width:6px; height:6px; background:var(--indigo-light);
  border-radius:50%; position:fixed; z-index:9999; pointer-events:none;
  transition: transform 0.1s var(--ease);
  mix-blend-mode: difference;
}}
.cursor-ring {{
  width:36px; height:36px; border:1.5px solid rgba(165,180,252,0.35);
  border-radius:50%; position:fixed; z-index:9998; pointer-events:none;
  transition: all 0.15s var(--ease);
}}

/* ═══════════════════════════════════════════════════════════════════════════
   NAVIGATION BAR
   ═══════════════════════════════════════════════════════════════════════════ */
.navbar {{
  position:sticky; top:0; z-index:100;
  display:flex; align-items:center; justify-content:space-between;
  padding:16px 0; margin-bottom:12px;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom:1px solid var(--border);
}}
.nav-brand {{
  display:flex; align-items:center; gap:10px;
  font-weight:800; font-size:15px; letter-spacing:-0.02em;
}}
.nav-logo {{
  width:32px; height:32px; border-radius:10px;
  background: linear-gradient(135deg, var(--indigo), var(--cyan));
  display:flex; align-items:center; justify-content:center;
  font-size:16px; color:white;
  animation: logoSpin 8s linear infinite;
}}
@keyframes logoSpin {{ 0%,100%{{transform:rotate(0)}} 50%{{transform:rotate(360deg)}} }}
.nav-links {{ display:flex; gap:6px; }}
.nav-link {{
  padding:7px 14px; border-radius:8px; font-size:12px; font-weight:600;
  color:var(--text-2); cursor:pointer; letter-spacing:0.02em;
  transition:all 0.25s var(--ease); border:1px solid transparent;
  text-decoration:none;
}}
.nav-link:hover {{ color:var(--text); background:var(--bg-hover); border-color:var(--border); }}
.nav-link.active {{ color:var(--indigo-light); background:rgba(99,102,241,0.1); border-color:rgba(99,102,241,0.25); }}
.nav-badge {{
  display:inline-flex; align-items:center; gap:5px;
  padding:5px 12px; border-radius:100px; font-size:11px; font-weight:600;
  background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.25);
  color:#6ee7b7; letter-spacing:0.04em;
}}
.nav-badge::before {{
  content:''; width:6px; height:6px; border-radius:50%;
  background:#6ee7b7; animation:blink 2s ease-in-out infinite;
}}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}

/* ═══════════════════════════════════════════════════════════════════════════
   HERO
   ═══════════════════════════════════════════════════════════════════════════ */
.hero {{
  text-align:center; padding:80px 0 56px;
  opacity:0; transform:translateY(30px);
}}
.hero-chip {{
  display:inline-flex; align-items:center; gap:8px;
  background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2);
  border-radius:100px; padding:6px 18px 6px 12px; margin-bottom:28px;
  font-size:12px; font-weight:600; color:var(--indigo-light);
  letter-spacing:0.06em; text-transform:uppercase;
}}
.hero-chip i {{ font-size:10px; animation: sparkle 2s ease infinite; }}
@keyframes sparkle {{
  0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:0.5;transform:scale(1.3)}}
}}
.hero h1 {{
  font-size:clamp(2.8rem,6vw,4.8rem); font-weight:900;
  letter-spacing:-0.04em; line-height:1.05;
  background:linear-gradient(135deg, #f1f5f9 0%, #a5b4fc 30%, #67e8f9 60%, #f1f5f9 100%);
  background-size:300% 300%;
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text;
  animation:shimmer 5s ease infinite;
  margin-bottom:18px;
}}
@keyframes shimmer {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}
.hero-sub {{
  font-size:1.1rem; color:var(--text-2); max-width:500px; margin:0 auto 36px;
  line-height:1.6; font-weight:400;
}}
.hero-stats {{
  display:inline-flex; gap:28px; padding:14px 28px;
  border:1px solid var(--border); border-radius:14px;
  background:var(--bg-card); backdrop-filter:blur(12px);
}}
.hero-stat {{ text-align:center; }}
.hero-stat-val {{ font-size:14px; font-weight:700; font-family:var(--mono); color:var(--text); }}
.hero-stat-lbl {{ font-size:10px; color:var(--text-3); text-transform:uppercase; letter-spacing:0.08em; margin-top:2px; }}

/* ═══════════════════════════════════════════════════════════════════════════
   SECTION HEADERS
   ═══════════════════════════════════════════════════════════════════════════ */
.section {{ padding:28px 0; opacity:0; transform:translateY(24px); }}
.section-head {{
  display:flex; align-items:center; gap:12px; margin-bottom:24px;
}}
.section-icon {{
  width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center;
  font-size:15px;
}}
.section-icon.purple {{ background:rgba(99,102,241,0.12); color:var(--indigo-light); }}
.section-icon.cyan   {{ background:rgba(6,182,212,0.12); color:var(--cyan-light); }}
.section-icon.amber  {{ background:rgba(245,158,11,0.12); color:var(--amber-light); }}
.section-label {{
  font-size:11px; font-weight:700; color:var(--text-3);
  text-transform:uppercase; letter-spacing:0.12em;
}}
.section-title {{
  font-size:20px; font-weight:800; letter-spacing:-0.02em; color:var(--text);
}}

/* ═══════════════════════════════════════════════════════════════════════════
   KPI CARDS
   ═══════════════════════════════════════════════════════════════════════════ */
.kpi-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }}
.kpi {{
  position:relative; overflow:hidden;
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); padding:28px;
  transition:all 0.4s var(--ease);
  cursor:default;
}}
.kpi::after {{
  content:''; position:absolute; inset:-1px; border-radius:var(--radius);
  background:linear-gradient(135deg,transparent 40%,rgba(99,102,241,0.15));
  opacity:0; transition:opacity 0.4s var(--ease); z-index:0;
}}
.kpi:hover {{ transform:translateY(-6px); border-color:var(--glow); }}
.kpi:hover::after {{ opacity:1; }}
.kpi>* {{ position:relative; z-index:1; }}
.kpi-top {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:18px; }}
.kpi-icon {{
  width:42px; height:42px; border-radius:12px;
  display:flex; align-items:center; justify-content:center;
  font-size:18px;
}}
.kpi-icon.i1 {{ background:linear-gradient(135deg,rgba(99,102,241,0.2),rgba(99,102,241,0.05)); color:var(--indigo-light); }}
.kpi-icon.i2 {{ background:linear-gradient(135deg,rgba(6,182,212,0.2),rgba(6,182,212,0.05)); color:var(--cyan-light); }}
.kpi-icon.i3 {{ background:linear-gradient(135deg,rgba(239,68,68,0.2),rgba(239,68,68,0.05)); color:#fca5a5; }}
.kpi-change {{
  font-size:11px; font-weight:600; padding:3px 8px; border-radius:6px;
  font-family:var(--mono);
}}
.kpi-change.up   {{ background:rgba(16,185,129,0.12); color:#6ee7b7; }}
.kpi-change.down {{ background:rgba(239,68,68,0.12); color:#fca5a5; }}
.kpi-val {{
  font-size:2.6rem; font-weight:900; letter-spacing:-0.04em;
  line-height:1; margin-bottom:6px;
  font-family:var(--sans);
}}
.kpi-lbl {{ font-size:12px; color:var(--text-3); font-weight:500; }}
.count-up {{ display:inline-block; }}

/* ═══════════════════════════════════════════════════════════════════════════
   SEGMENT CARDS (with 3D tilt)
   ═══════════════════════════════════════════════════════════════════════════ */
.seg-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }}
.seg {{
  position:relative; overflow:hidden; cursor:pointer;
  border:1px solid var(--border); border-radius:var(--radius);
  padding:24px 22px; transition:all 0.4s var(--ease);
  transform-style:preserve-3d;
}}
.seg::before {{
  content:''; position:absolute; top:0; left:0; right:0; height:3px;
  border-radius:var(--radius) var(--radius) 0 0;
}}
.seg.champions  {{ background:rgba(99,102,241,0.06);  }}
.seg.champions::before  {{ background:linear-gradient(90deg,var(--indigo),#818cf8); }}
.seg.promising      {{ background:rgba(6,182,212,0.05);   }}
.seg.promising::before      {{ background:linear-gradient(90deg,var(--cyan),#22d3ee);   }}
.seg.atrisk     {{ background:rgba(245,158,11,0.05);  }}
.seg.atrisk::before     {{ background:linear-gradient(90deg,var(--amber),#fbbf24);  }}
.seg.hibernating{{ background:rgba(100,116,139,0.05); }}
.seg.hibernating::before{{ background:linear-gradient(90deg,var(--slate),#94a3b8);  }}
.seg:hover {{ transform:translateY(-4px) scale(1.02); }}
.seg-emoji {{ font-size:2rem; margin-bottom:14px; display:block; }}
.seg-name  {{ font-size:13px; font-weight:700; margin-bottom:2px; }}
.seg.champions .seg-name   {{ color:var(--indigo-light); }}
.seg.promising .seg-name       {{ color:var(--cyan-light); }}
.seg.atrisk .seg-name      {{ color:var(--amber-light); }}
.seg.hibernating .seg-name {{ color:var(--slate-light); }}
.seg-num {{
  font-size:2.4rem; font-weight:900; letter-spacing:-0.04em;
  margin-bottom:4px; line-height:1;
}}
.seg-meta {{ font-size:11px; color:var(--text-3); line-height:1.5; }}
.seg-bar {{
  margin-top:14px; height:4px; border-radius:2px;
  background:rgba(255,255,255,0.05); overflow:hidden;
}}
.seg-bar-fill {{
  height:100%; border-radius:2px; width:0%;
  transition:width 1.2s var(--ease);
}}
.seg.champions .seg-bar-fill   {{ background:var(--indigo); }}
.seg.promising .seg-bar-fill       {{ background:var(--cyan); }}
.seg.atrisk .seg-bar-fill      {{ background:var(--amber); }}
.seg.hibernating .seg-bar-fill {{ background:var(--slate); }}
.seg-tag {{
  display:inline-flex; align-items:center; gap:4px;
  margin-top:12px; font-size:10px; font-weight:700;
  padding:4px 10px; border-radius:6px;
  text-transform:uppercase; letter-spacing:0.06em;
}}
.seg.champions .seg-tag   {{ background:rgba(99,102,241,0.15); color:var(--indigo-light); }}
.seg.promising .seg-tag       {{ background:rgba(6,182,212,0.15); color:var(--cyan-light); }}
.seg.atrisk .seg-tag      {{ background:rgba(245,158,11,0.15); color:var(--amber-light); }}
.seg.hibernating .seg-tag {{ background:rgba(100,116,139,0.15); color:var(--slate-light); }}

/* ═══════════════════════════════════════════════════════════════════════════
   CHART CONTAINERS
   ═══════════════════════════════════════════════════════════════════════════ */
.charts {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.chart-box {{
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); padding:24px;
  transition:all 0.35s var(--ease);
}}
.chart-box:hover {{ background:var(--bg-hover); border-color:rgba(99,102,241,0.2); }}
.chart-head {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:18px; }}
.chart-title {{ font-size:14px; font-weight:700; }}
.chart-sub   {{ font-size:11px; color:var(--text-3); margin-top:2px; }}
.chart-badge {{
  font-size:10px; font-weight:600; padding:4px 10px; border-radius:6px;
  background:rgba(99,102,241,0.1); color:var(--indigo-light);
  letter-spacing:0.04em; text-transform:uppercase;
}}

/* ═══════════════════════════════════════════════════════════════════════════
   ACTION CARDS (playbook)
   ═══════════════════════════════════════════════════════════════════════════ */
.playbook-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:14px; }}
.play {{
  border:1px solid var(--border); border-radius:var(--radius);
  padding:22px; position:relative; overflow:hidden;
  transition:all 0.35s var(--ease);
}}
.play::before {{
  content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
}}
.play:hover {{ transform:translateY(-3px); }}
.play.champions  {{ background:rgba(99,102,241,0.05); }}
.play.champions::before  {{ background:var(--indigo); }}
.play.champions:hover    {{ border-color:rgba(99,102,241,0.3); box-shadow:0 16px 48px rgba(99,102,241,0.12); }}
.play.promising      {{ background:rgba(6,182,212,0.04); }}
.play.promising::before      {{ background:var(--cyan); }}
.play.promising:hover        {{ border-color:rgba(6,182,212,0.3); box-shadow:0 16px 48px rgba(6,182,212,0.1); }}
.play.atrisk     {{ background:rgba(245,158,11,0.04); }}
.play.atrisk::before     {{ background:var(--amber); }}
.play.atrisk:hover       {{ border-color:rgba(245,158,11,0.3); box-shadow:0 16px 48px rgba(245,158,11,0.1); }}
.play.hibernating{{ background:rgba(100,116,139,0.04); }}
.play.hibernating::before{{ background:var(--slate); }}
.play.hibernating:hover  {{ border-color:rgba(100,116,139,0.25); box-shadow:0 16px 48px rgba(100,116,139,0.08); }}
.play-head {{ display:flex; align-items:center; gap:10px; margin-bottom:10px; }}
.play-emoji {{ font-size:1.4rem; }}
.play-name {{ font-size:13px; font-weight:700; }}
.play.champions .play-name   {{ color:var(--indigo-light); }}
.play.promising .play-name       {{ color:var(--cyan-light); }}
.play.atrisk .play-name      {{ color:var(--amber-light); }}
.play.hibernating .play-name {{ color:var(--slate-light); }}
.play-text {{ font-size:13px; color:var(--text-2); line-height:1.6; }}
.play-metrics {{ display:flex; gap:16px; margin-top:14px; }}
.play-metric {{
  font-size:11px; color:var(--text-3); font-weight:600;
  display:flex; align-items:center; gap:5px;
}}
.play-metric span {{ font-family:var(--mono); color:var(--text-2); font-weight:700; }}

/* ═══════════════════════════════════════════════════════════════════════════
   DATA TABLE
   ═══════════════════════════════════════════════════════════════════════════ */
.table-wrap {{
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); overflow:hidden;
}}
.table-toolbar {{
  display:flex; align-items:center; justify-content:space-between;
  padding:16px 20px; border-bottom:1px solid var(--border);
}}
.table-toolbar h3 {{ font-size:14px; font-weight:700; }}
.table-filter {{
  display:flex; gap:6px;
}}
.filter-btn {{
  padding:5px 12px; border-radius:7px; font-size:11px; font-weight:600;
  border:1px solid var(--border); background:transparent; color:var(--text-2);
  cursor:pointer; transition:all 0.2s var(--ease); font-family:var(--sans);
}}
.filter-btn:hover {{ background:var(--bg-hover); color:var(--text); }}
.filter-btn.active {{ background:rgba(99,102,241,0.12); border-color:rgba(99,102,241,0.3); color:var(--indigo-light); }}
table {{
  width:100%; border-collapse:collapse; font-size:13px;
}}
thead th {{
  padding:12px 16px; text-align:left; font-size:10px; font-weight:700;
  color:var(--text-3); text-transform:uppercase; letter-spacing:0.1em;
  border-bottom:1px solid var(--border); position:sticky; top:0;
  background:var(--bg);
}}
tbody td {{
  padding:11px 16px; border-bottom:1px solid rgba(255,255,255,0.03);
  transition:background 0.15s ease;
}}
tbody tr {{ transition:background 0.15s ease; }}
tbody tr:hover {{ background:var(--bg-hover); }}
.seg-pill {{
  display:inline-block; padding:3px 10px; border-radius:6px;
  font-size:10px; font-weight:700; text-transform:uppercase;
  letter-spacing:0.04em;
}}
.seg-pill.champions   {{ background:rgba(99,102,241,0.15); color:var(--indigo-light); }}
.seg-pill.promising       {{ background:rgba(6,182,212,0.15); color:var(--cyan-light); }}
.seg-pill.atrisk      {{ background:rgba(245,158,11,0.15); color:var(--amber-light); }}
.seg-pill.hibernating {{ background:rgba(100,116,139,0.15); color:var(--slate-light); }}
td.mono {{ font-family:var(--mono); font-size:12px; font-weight:500; }}
.table-body {{ max-height:400px; overflow-y:auto; }}

/* ═══════════════════════════════════════════════════════════════════════════
   FOOTER
   ═══════════════════════════════════════════════════════════════════════════ */
.footer {{
  text-align:center; padding:48px 0 16px;
  border-top:1px solid var(--border); margin-top:48px;
}}
.footer-brand {{ font-size:14px; font-weight:700; margin-bottom:8px; }}
.footer-sub   {{ font-size:12px; color:var(--text-3); }}
.footer-sub span {{ color:var(--indigo-light); }}
.footer-links {{ display:flex; justify-content:center; gap:20px; margin-top:16px; }}
.footer-link {{
  font-size:11px; color:var(--text-3); text-decoration:none;
  transition:color 0.2s; font-weight:500;
}}
.footer-link:hover {{ color:var(--indigo-light); }}

/* ═══════════════════ Responsive ═══════════════════ */
@media(max-width:900px){{
  .kpi-grid,.charts,.playbook-grid {{ grid-template-columns:1fr; }}
  .seg-grid {{ grid-template-columns:1fr 1fr; }}
  .hero h1 {{ font-size:2rem; }}
}}
@media(max-width:600px){{
  .seg-grid {{ grid-template-columns:1fr; }}
  .app {{ padding:0 16px 32px; }}
}}
</style>
</head>
<body>
<!-- Animated background -->
<div class="mesh-bg"></div>
<canvas id="particles"></canvas>

<!-- Custom Cursor -->
<div class="cursor-dot" id="cursorDot"></div>
<div class="cursor-ring" id="cursorRing"></div>

<div class="app">

<!-- ═══ NAVBAR ═══ -->
<nav class="navbar" id="navbar">
  <div class="nav-brand">
    <div class="nav-logo"><i class="fa-solid fa-bolt"></i></div>
    SegmentIQ
  </div>
  <div class="nav-links">
    <a class="nav-link active" href="#overview">Overview</a>
    <a class="nav-link" href="#segments">Segments</a>
    <a class="nav-link" href="#analytics">Analytics</a>
    <a class="nav-link" href="#playbook">Playbook</a>
    <a class="nav-link" href="#data">Data</a>
  </div>
</nav>

<!-- ═══ HERO ═══ -->
<section class="hero" id="heroSection">
  <div class="hero-chip"><i class="fa-solid fa-sparkles"></i> RFM &middot; K-Means &middot; Refreshed: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%b %d, %H:%M")} IST</div>
  <h1>Customer Intelligence<br>Platform</h1>
  <p class="hero-sub">AI-powered segmentation revealing which customers to retain, grow, and win back — and exactly how.</p>
  <div class="hero-stats">
    <div class="hero-stat"><div class="hero-stat-val">4 Segments</div><div class="hero-stat-lbl">Active</div></div>
    <div class="hero-stat"><div class="hero-stat-val">K=4</div><div class="hero-stat-lbl">Optimal K</div></div>
    <div class="hero-stat"><div class="hero-stat-val">DuckDB</div><div class="hero-stat-lbl">Warehouse</div></div>
    <div class="hero-stat"><div class="hero-stat-val">dbt + dlt</div><div class="hero-stat-lbl">Pipeline</div></div>
  </div>
</section>

<!-- ═══ KPIs ═══ -->
<section class="section" id="overview">
  <div class="section-head">
    <div class="section-icon purple"><i class="fa-solid fa-chart-line"></i></div>
    <div><div class="section-label">Portfolio Overview</div><div class="section-title">Key Performance Indicators</div></div>
  </div>
  <div class="kpi-grid">
    <div class="kpi" data-tilt data-tilt-max="4" data-tilt-speed="400" data-tilt-glare data-tilt-max-glare="0.08">
      <div class="kpi-top">
        <div class="kpi-icon i1"><i class="fa-solid fa-users"></i></div>
        <span class="kpi-change up"><i class="fa-solid fa-arrow-up" style="font-size:9px"></i> Active</span>
      </div>
      <div class="kpi-val"><span class="count-up" data-target="{total_customers}">0</span></div>
      <div class="kpi-lbl">Total Customers</div>
    </div>
    <div class="kpi" data-tilt data-tilt-max="4" data-tilt-speed="400" data-tilt-glare data-tilt-max-glare="0.08">
      <div class="kpi-top">
        <div class="kpi-icon i2"><i class="fa-solid fa-coins"></i></div>
        <span class="kpi-change up"><i class="fa-solid fa-arrow-up" style="font-size:9px"></i> Lifetime</span>
      </div>
      <div class="kpi-val">$<span class="count-up" data-target="{int(total_revenue)}" data-format="currency">0</span></div>
      <div class="kpi-lbl">Total Revenue</div>
    </div>
    <div class="kpi" data-tilt data-tilt-max="4" data-tilt-speed="400" data-tilt-glare data-tilt-max-glare="0.08">
      <div class="kpi-top">
        <div class="kpi-icon i3"><i class="fa-solid fa-triangle-exclamation"></i></div>
        <span class="kpi-change down"><i class="fa-solid fa-arrow-down" style="font-size:9px"></i> {at_risk_pct}%</span>
      </div>
      <div class="kpi-val">$<span class="count-up" data-target="{int(at_risk_revenue)}" data-format="currency">0</span></div>
      <div class="kpi-lbl">Revenue at Risk</div>
    </div>
  </div>
</section>

<!-- ═══ SEGMENTS ═══ -->
<section class="section" id="segments">
  <div class="section-head">
    <div class="section-icon cyan"><i class="fa-solid fa-layer-group"></i></div>
    <div><div class="section-label">Customer Segments</div><div class="section-title">Behavioral Clusters</div></div>
  </div>
  <div class="seg-grid" id="segGrid"></div>
</section>

<!-- ═══ CHARTS ═══ -->
<section class="section" id="analytics">
  <div class="section-head">
    <div class="section-icon purple"><i class="fa-solid fa-chart-pie"></i></div>
    <div><div class="section-label">Analytics</div><div class="section-title">Visual Intelligence</div></div>
  </div>
  <div class="charts">
    <div class="chart-box">
      <div class="chart-head">
        <div><div class="chart-title">Revenue Distribution</div><div class="chart-sub">Monetary share per segment</div></div>
        <span class="chart-badge"><i class="fa-solid fa-chart-pie" style="font-size:9px"></i> Donut</span>
      </div>
      <canvas id="donutChart" height="260"></canvas>
    </div>
    <div class="chart-box">
      <div class="chart-head">
        <div><div class="chart-title">Recency vs Monetary</div><div class="chart-sub">Customer scatter · bubble = frequency</div></div>
        <span class="chart-badge"><i class="fa-solid fa-braille" style="font-size:9px"></i> Scatter</span>
      </div>
      <canvas id="scatterChart" height="260"></canvas>
    </div>
    <div class="chart-box">
      <div class="chart-head">
        <div><div class="chart-title">Customer Volume</div><div class="chart-sub">Customers per segment</div></div>
        <span class="chart-badge"><i class="fa-solid fa-chart-bar" style="font-size:9px"></i> Bar</span>
      </div>
      <canvas id="barChart" height="260"></canvas>
    </div>
    <div class="chart-box">
      <div class="chart-head">
        <div><div class="chart-title">RFM Profile Radar</div><div class="chart-sub">Normalized avg metrics</div></div>
        <span class="chart-badge"><i class="fa-solid fa-diagram-project" style="font-size:9px"></i> Radar</span>
      </div>
      <canvas id="radarChart" height="260"></canvas>
    </div>
    <div class="chart-box" style="grid-column: 1 / -1; max-width: 600px; margin: 0 auto; width: 100%;">
      <div class="chart-head">
        <div><div class="chart-title">Model Selection (Elbow Method)</div><div class="chart-sub">Justifying K=4 clusters via WCSS</div></div>
        <span class="chart-badge"><i class="fa-solid fa-square-root-variable" style="font-size:9px"></i> WCSS</span>
      </div>
      <canvas id="elbowChart" height="220"></canvas>
    </div>
  </div>
</section>

<!-- ═══ PLAYBOOK ═══ -->
<section class="section" id="playbook">
  <div class="section-head">
    <div class="section-icon amber"><i class="fa-solid fa-bullseye"></i></div>
    <div><div class="section-label">Strategic Playbook</div><div class="section-title">Recommended Actions</div></div>
  </div>
  <div class="playbook-grid" id="playbookGrid"></div>
</section>

<!-- ═══ DATA TABLE ═══ -->
<section class="section" id="data">
  <div class="section-head">
    <div class="section-icon cyan"><i class="fa-solid fa-table"></i></div>
    <div><div class="section-label">Customer Data</div><div class="section-title">Top Customers by Segment</div></div>
  </div>
  <div class="table-wrap">
    <div class="table-toolbar">
      <h3><i class="fa-solid fa-database" style="margin-right:8px;color:var(--indigo-light)"></i> Segment Explorer</h3>
      <div class="table-filter" id="tableFilter">
        <button id="exportCsvBtn" class="filter-btn" style="margin-right:8px; border-color:var(--indigo-light); color:var(--indigo-light)"><i class="fa-solid fa-download"></i> Export CSV</button>
        <button class="filter-btn active" data-seg="all">All</button>
        <button class="filter-btn" data-seg="Champions">Champions</button>
        <button class="filter-btn" data-seg="Promising">Promising</button>
        <button class="filter-btn" data-seg="At-Risk High-Value">At-Risk</button>
        <button class="filter-btn" data-seg="Hibernating">Hibernating</button>
      </div>
    </div>
    <div class="table-body">
      <table>
        <thead><tr>
          <th>Customer ID</th><th>Recency</th><th>Frequency</th><th>Monetary</th><th>Segment</th>
        </tr></thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </div>
</section>

<!-- ═══ FOOTER ═══ -->
<div class="footer">
  <div class="footer-brand"><i class="fa-solid fa-bolt" style="color:var(--indigo-light)"></i> SegmentIQ</div>
  <div class="footer-sub">Built with <span>&hearts;</span> &middot; UCI Online Retail &middot; RFM + K-Means &middot; dlt &middot; dbt &middot; DuckDB</div>
  <div class="footer-links">
    <a class="footer-link" href="#overview">Overview</a>
    <a class="footer-link" href="#segments">Segments</a>
    <a class="footer-link" href="#analytics">Analytics</a>
    <a class="footer-link" href="#playbook">Playbook</a>
  </div>
</div>

</div><!-- end .app -->

<script>
// ═══════════════════════════════════════════════════════════════════════════
//  DATA
// ═══════════════════════════════════════════════════════════════════════════
const D = {dashboard_data};
const SEG_COLORS = ['#6366f1','#06b6d4','#f59e0b','#64748b'];
const SEG_COLORS_ALPHA = ['rgba(99,102,241,0.5)','rgba(6,182,212,0.5)','rgba(245,158,11,0.5)','rgba(100,116,139,0.5)'];
const SEG_CSS = ['champions','promising','atrisk','hibernating'];
const SEG_EMOJI = ['🏆','💎','⚠️','🌙'];
const SEG_TAGS = ['RETAIN','GROW','WIN BACK','MINIMAL'];

// ═══════════════════════════════════════════════════════════════════════════
//  PARTICLES
// ═══════════════════════════════════════════════════════════════════════════
(function(){{
  const c = document.getElementById('particles');
  const ctx = c.getContext('2d');
  let w, h, particles = [];
  function resize() {{ w = c.width = window.innerWidth; h = c.height = window.innerHeight; }}
  resize(); window.addEventListener('resize', resize);
  for(let i=0; i<60; i++) {{
    particles.push({{
      x: Math.random()*w, y: Math.random()*h,
      vx: (Math.random()-0.5)*0.3, vy: (Math.random()-0.5)*0.3,
      r: Math.random()*1.5+0.5, a: Math.random()*0.3+0.1
    }});
  }}
  function draw() {{
    ctx.clearRect(0,0,w,h);
    particles.forEach((p,i) => {{
      p.x += p.vx; p.y += p.vy;
      if(p.x<0) p.x=w; if(p.x>w) p.x=0;
      if(p.y<0) p.y=h; if(p.y>h) p.y=0;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle = `rgba(165,180,252,${{p.a}})`;
      ctx.fill();
      // Connect nearby
      for(let j=i+1;j<particles.length;j++) {{
        const dx=p.x-particles[j].x, dy=p.y-particles[j].y;
        const dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<120) {{
          ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(particles[j].x,particles[j].y);
          ctx.strokeStyle = `rgba(165,180,252,${{0.06*(1-dist/120)}})`;
          ctx.lineWidth = 0.5; ctx.stroke();
        }}
      }}
    }});
    requestAnimationFrame(draw);
  }}
  draw();
}})();

// ═══════════════════════════════════════════════════════════════════════════
//  CUSTOM CURSOR
// ═══════════════════════════════════════════════════════════════════════════
const dot = document.getElementById('cursorDot');
const ring = document.getElementById('cursorRing');
let mx=0, my=0;
document.addEventListener('mousemove', e => {{
  mx=e.clientX; my=e.clientY;
  dot.style.left = mx-3+'px'; dot.style.top = my-3+'px';
}});
function followCursor() {{
  const rx = parseFloat(ring.style.left||mx) || mx;
  const ry = parseFloat(ring.style.top||my) || my;
  ring.style.left = rx+(mx-rx-18)*0.12+'px';
  ring.style.top  = ry+(my-ry-18)*0.12+'px';
  requestAnimationFrame(followCursor);
}}
followCursor();
// Hover glow on interactive elements
document.querySelectorAll('.kpi,.seg,.play,.filter-btn,.nav-link,.chart-box').forEach(el => {{
  el.addEventListener('mouseenter', () => {{
    ring.style.width='52px'; ring.style.height='52px';
    ring.style.borderColor='rgba(165,180,252,0.6)';
  }});
  el.addEventListener('mouseleave', () => {{
    ring.style.width='36px'; ring.style.height='36px';
    ring.style.borderColor='rgba(165,180,252,0.35)';
  }});
}});

// ═══════════════════════════════════════════════════════════════════════════
//  GSAP ANIMATIONS
// ═══════════════════════════════════════════════════════════════════════════
gsap.registerPlugin(ScrollTrigger);

// Hero entrance
gsap.to('#heroSection', {{
  opacity:1, y:0, duration:1, ease:'power3.out', delay:0.3
}});

// Sections stagger in on scroll
document.querySelectorAll('.section').forEach(sec => {{
  gsap.to(sec, {{
    scrollTrigger: {{ trigger:sec, start:'top 85%', toggleActions:'play none none none' }},
    opacity:1, y:0, duration:0.7, ease:'power3.out'
  }});
}});

// ═══════════════════════════════════════════════════════════════════════════
//  COUNT-UP ANIMATION
// ═══════════════════════════════════════════════════════════════════════════
function animateCounters() {{
  document.querySelectorAll('.count-up').forEach(el => {{
    const target = parseInt(el.dataset.target);
    const fmt = el.dataset.format;
    const dur = 2;
    gsap.to({{ val: 0 }}, {{
      val: target, duration: dur, ease: 'power2.out',
      onUpdate: function() {{
        const v = Math.round(this.targets()[0].val);
        el.textContent = fmt === 'currency' ? v.toLocaleString() : v.toLocaleString();
      }}
    }});
  }});
}}
setTimeout(animateCounters, 600);

// ═══════════════════════════════════════════════════════════════════════════
//  SEGMENT CARDS
// ═══════════════════════════════════════════════════════════════════════════
const segGrid = document.getElementById('segGrid');
D.segments.forEach((s,i) => {{
  const cls = SEG_CSS[i];
  const card = document.createElement('div');
  card.className = `seg ${{cls}}`;
  card.setAttribute('data-tilt',''); card.setAttribute('data-tilt-max','6');
  card.setAttribute('data-tilt-speed','400'); card.setAttribute('data-tilt-glare','');
  card.setAttribute('data-tilt-max-glare','0.06');
  card.innerHTML = `
    <span class="seg-emoji">${{SEG_EMOJI[i]}}</span>
    <div class="seg-name">${{s.name}}</div>
    <div class="seg-num">${{s.count.toLocaleString()}}</div>
    <div class="seg-meta">${{s.pct}}% of customers &middot; ${{s.rev_pct}}% revenue</div>
    <div class="seg-bar"><div class="seg-bar-fill" data-width="${{s.pct}}"></div></div>
    <span class="seg-tag"><i class="fa-solid fa-crosshairs" style="font-size:9px"></i>&nbsp;${{SEG_TAGS[i]}}</span>
  `;
  segGrid.appendChild(card);
}});

// Animate segment bars
setTimeout(() => {{
  document.querySelectorAll('.seg-bar-fill').forEach(bar => {{
    bar.style.width = bar.dataset.width + '%';
  }});
}}, 800);

// Re-init tilt
VanillaTilt.init(document.querySelectorAll("[data-tilt]"), {{
  max: 6, speed: 400, glare: true, 'max-glare': 0.06
}});

// ═══════════════════════════════════════════════════════════════════════════
//  CHARTS (Chart.js)
// ═══════════════════════════════════════════════════════════════════════════
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = '#94a3b8';

// Donut
new Chart(document.getElementById('donutChart'), {{
  type: 'doughnut',
  data: {{
    labels: D.segments.map(s => s.name),
    datasets: [{{
      data: D.segments.map(s => s.revenue),
      backgroundColor: SEG_COLORS,
      borderColor: '#06060f', borderWidth: 4,
      hoverOffset: 12,
    }}]
  }},
  options: {{
    cutout: '72%', responsive: true,
    plugins: {{
      legend: {{ position:'bottom', labels: {{ padding:16, usePointStyle:true, pointStyleWidth:8, font:{{size:11,weight:600}} }} }},
      tooltip: {{ backgroundColor:'#1e293b', titleFont:{{weight:700}}, bodyFont:{{size:12}}, cornerRadius:10, padding:12,
        callbacks: {{ label: ctx => ' $'+ctx.parsed.toLocaleString() }} }}
    }},
    animation: {{ animateRotate:true, animateScale:true, duration:1200, easing:'easeOutQuart' }}
  }}
}});

// Scatter (bubble)
const scatterColors = SEG_COLORS;
const scatterSets = [[], [], [], []];
D.scatter.forEach(pt => scatterSets[pt.seg].push({{ x:pt.x, y:pt.y, r:pt.r }}));
new Chart(document.getElementById('scatterChart'), {{
  type: 'bubble',
  data: {{
    datasets: scatterSets.map((pts, i) => ({{
      label: D.segments[i].name,
      data: pts,
      backgroundColor: SEG_COLORS_ALPHA[i],
      borderColor: SEG_COLORS[i],
      borderWidth: 1,
    }}))
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display:false }},
      tooltip: {{
        backgroundColor:'#1e293b', cornerRadius:10, padding:12,
        callbacks: {{ label: ctx => `${{ctx.dataset.label}} · R:${{ctx.parsed.x}}d · $${{ctx.parsed.y.toLocaleString()}}` }}
      }}
    }},
    scales: {{
      x: {{ title: {{ display:true, text:'Recency (days)', font:{{size:11}} }}, grid: {{ color:'rgba(255,255,255,0.04)' }}, border:{{ color:'rgba(255,255,255,0.06)' }} }},
      y: {{ title: {{ display:true, text:'Monetary ($)', font:{{size:11}} }}, grid: {{ color:'rgba(255,255,255,0.04)' }}, border:{{ color:'rgba(255,255,255,0.06)' }} }}
    }},
    animation: {{ duration:1400, easing:'easeOutQuart' }}
  }}
}});

// Bar chart
new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: {{
    labels: D.segments.map(s => s.name),
    datasets: [{{
      data: D.segments.map(s => s.count),
      backgroundColor: SEG_COLORS.map(c => c+'22'),
      borderColor: SEG_COLORS,
      borderWidth: 1.5,
      borderRadius: 8, borderSkipped: false,
    }}]
  }},
  options: {{
    indexAxis: 'y', responsive: true,
    plugins: {{
      legend: {{ display:false }},
      tooltip: {{ backgroundColor:'#1e293b', cornerRadius:10, padding:12, callbacks:{{ label: ctx => ' '+ctx.parsed.x.toLocaleString()+' customers' }} }}
    }},
    scales: {{
      x: {{ grid: {{ color:'rgba(255,255,255,0.04)' }}, border:{{ color:'rgba(255,255,255,0.06)' }} }},
      y: {{ grid: {{ display:false }}, border:{{ display:false }}, ticks:{{ font:{{size:11,weight:600}} }} }}
    }},
    animation: {{ duration:1200, easing:'easeOutQuart' }}
  }}
}});

// Radar
const maxR = Math.max(...D.segments.map(s=>s.avg_recency));
const maxF = Math.max(...D.segments.map(s=>s.avg_frequency));
const maxM = Math.max(...D.segments.map(s=>s.avg_monetary));
new Chart(document.getElementById('radarChart'), {{
  type: 'radar',
  data: {{
    labels: ['Recency (inv)', 'Frequency', 'Monetary'],
    datasets: D.segments.map((s,i) => ({{
      label: s.name,
      data: [
        +((1 - s.avg_recency/maxR)*100).toFixed(1),
        +((s.avg_frequency/maxF)*100).toFixed(1),
        +((s.avg_monetary/maxM)*100).toFixed(1)
      ],
      borderColor: SEG_COLORS[i], backgroundColor: SEG_COLORS[i]+'18',
      borderWidth: 2, pointRadius: 3, pointBackgroundColor: SEG_COLORS[i],
    }}))
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ position:'bottom', labels: {{ padding:14, usePointStyle:true, pointStyleWidth:8, font:{{size:11,weight:600}} }} }},
      tooltip: {{ backgroundColor:'#1e293b', cornerRadius:10, padding:12 }}
    }},
    scales: {{
      r: {{ min:0, max:100, ticks:{{ display:false }}, grid:{{ color:'rgba(255,255,255,0.06)' }}, angleLines:{{ color:'rgba(255,255,255,0.06)' }}, pointLabels:{{ font:{{size:11,weight:600}}, color:'#94a3b8' }} }}
    }},
    animation: {{ duration:1200, easing:'easeOutQuart' }}
  }}
}});

// Elbow Method (K-Selection Evidence)
const wcssData = [13014, 9014, 5441, 4096, 3120, 2503, 2023, 1716, 1446];
new Chart(document.getElementById('elbowChart'), {{
  type: 'line',
  data: {{
    labels: [1, 2, 3, 4, 5, 6, 7, 8, 9],
    datasets: [{{
      label: 'WCSS (Inertia)',
      data: wcssData,
      borderColor: '#a5b4fc',
      backgroundColor: 'rgba(165,180,252,0.1)',
      borderWidth: 3,
      pointBackgroundColor: '#6366f1',
      pointBorderColor: '#fff',
      pointRadius: [4, 4, 4, 8, 4, 4, 4, 4, 4],
      pointHoverRadius: 10,
      fill: true,
      tension: 0.3
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ backgroundColor:'#1e293b', cornerRadius:10, padding:12 }}
    }},
    scales: {{
      x: {{ title: {{ display:true, text:'Number of Clusters (K)', font:{{size:11}} }}, grid: {{ color:'rgba(255,255,255,0.04)' }} }},
      y: {{ title: {{ display:true, text:'Within-Cluster Sum of Squares', font:{{size:11}} }}, grid: {{ color:'rgba(255,255,255,0.04)' }} }}
    }},
    animation: {{ duration:1200, easing:'easeOutQuart' }}
  }}
}});

// ═══════════════════════════════════════════════════════════════════════════
//  PLAYBOOK
// ═══════════════════════════════════════════════════════════════════════════
const pbGrid = document.getElementById('playbookGrid');
D.segments.forEach((s,i) => {{
  const div = document.createElement('div');
  div.className = `play ${{SEG_CSS[i]}}`;
  div.innerHTML = `
    <div class="play-head">
      <span class="play-emoji">${{SEG_EMOJI[i]}}</span>
      <span class="play-name">${{s.name}}</span>
    </div>
    <div class="play-text">${{s.action}}</div>
    <div class="play-metrics">
      <div class="play-metric"><i class="fa-solid fa-clock" style="font-size:10px"></i> <span>${{s.avg_recency}}d</span> recency</div>
      <div class="play-metric"><i class="fa-solid fa-repeat" style="font-size:10px"></i> <span>${{s.avg_frequency}}</span> freq</div>
      <div class="play-metric"><i class="fa-solid fa-dollar-sign" style="font-size:10px"></i> <span>$${{Math.round(s.avg_monetary).toLocaleString()}}</span> avg</div>
    </div>
  `;
  pbGrid.appendChild(div);
}});

// ═══════════════════════════════════════════════════════════════════════════
//  DATA TABLE (with filter)
// ═══════════════════════════════════════════════════════════════════════════
const tbody = document.getElementById('tableBody');
const filterBtns = document.querySelectorAll('#tableFilter .filter-btn');
let currentFilter = 'all';

function renderTable(filter) {{
  tbody.innerHTML = '';
  const rows = filter === 'all' ? D.table : D.table.filter(r => r.seg === filter);
  rows.forEach((r, idx) => {{
    const cls = SEG_CSS[D.segments.findIndex(s => s.name === r.seg)];
    const tr = document.createElement('tr');
    tr.style.opacity = '0'; tr.style.transform = 'translateX(-10px)';
    tr.innerHTML = `
      <td class="mono">#${{r.id}}</td>
      <td class="mono">${{r.r}}d</td>
      <td class="mono">${{r.f}}</td>
      <td class="mono">$${{r.m.toLocaleString()}}</td>
      <td><span class="seg-pill ${{cls||''}}">${{r.seg}}</span></td>
    `;
    tbody.appendChild(tr);
    // Stagger animation
    setTimeout(() => {{ tr.style.transition='all 0.3s cubic-bezier(0.22,1,0.36,1)'; tr.style.opacity='1'; tr.style.transform='translateX(0)'; }}, idx*30);
  }});
}}
renderTable('all');

filterBtns.forEach(btn => {{
  if (btn.id === 'exportCsvBtn') return; // Handled separately
  btn.addEventListener('click', () => {{
    filterBtns.forEach(b => {{
      if (b.id !== 'exportCsvBtn') b.classList.remove('active');
    }});
    btn.classList.add('active');
    currentFilter = btn.dataset.seg;
    renderTable(currentFilter);
  }});
}});

// CSV Export Logic
document.getElementById('exportCsvBtn').addEventListener('click', () => {{
  let csv = 'Customer ID,Recency,Frequency,Monetary,Segment\\n';
  const rows = currentFilter === 'all' ? D.table : D.table.filter(r => r.seg === currentFilter);
  rows.forEach(r => {{
      csv += `${{r.id}},${{r.r}},${{r.f}},${{r.m}},${{r.seg}}\\n`;
  }});
  const blob = new Blob([csv], {{ type: 'text/csv' }});
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `segment_export_${{currentFilter}}.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}});

// ═══════════════════════════════════════════════════════════════════════════
//  NAV SMOOTH SCROLL + ACTIVE STATE
// ═══════════════════════════════════════════════════════════════════════════
document.querySelectorAll('.nav-link').forEach(link => {{
  link.addEventListener('click', e => {{
    e.preventDefault();
    const target = document.querySelector(link.getAttribute('href'));
    if(target) target.scrollIntoView({{ behavior:'smooth', block:'start' }});
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    link.classList.add('active');
  }});
}});

// Intersection Observer for active nav
const sections = document.querySelectorAll('.section, .hero');
const observer = new IntersectionObserver(entries => {{
  entries.forEach(entry => {{
    if(entry.isIntersecting) {{
      const id = entry.target.id;
      document.querySelectorAll('.nav-link').forEach(l => {{
        l.classList.toggle('active', l.getAttribute('href') === '#'+id);
      }});
    }}
  }});
}}, {{ threshold: 0.3 }});
sections.forEach(s => observer.observe(s));

</script>
</body>
</html>
"""

components.html(html_content, height=4200, scrolling=True)
