"""
FanIQ - Know your fans. Act on the insight.
Sport-agnostic fan segmentation and campaign intelligence platform.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io, random, os, time
from fpdf import FPDF
from generate_sample import generate_sample_data, generate_template

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FanIQ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

[data-testid="stAppViewContainer"] { background: #08080c !important; }
[data-testid="stHeader"]           { background: #08080c !important; border-bottom: 1px solid #1a1a22; }
section[data-testid="stSidebar"]   { display: none; }
.block-container { padding: 1rem 2.5rem 3rem !important; max-width: 1440px !important; }

/* Tabs */
[data-testid="stTabs"] > div:first-child { border-bottom: 1px solid #23232b; gap: 4px; }
button[data-baseweb="tab"] {
    color: #8b8b95 !important; font-size: 13px !important; font-weight: 600 !important;
    padding: 11px 18px !important; border: none !important; background: transparent !important;
}
button[data-baseweb="tab"]:hover { color: #C8F135 !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #0a0a0f !important; background: #C8F135 !important;
    border-radius: 8px 8px 0 0 !important; font-weight: 700 !important;
}
[data-testid="stTabsContent"] { padding-top: 1.75rem !important; }

/* Inputs */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { background: #101018 !important; color: #e5e7eb !important; border: 1px solid #2a2a34 !important; }
[data-testid="stSelectbox"] > div > div { background: #101018 !important; color: #e5e7eb !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: #101018 !important; border: 1.5px dashed #C8F135 !important;
    border-radius: 14px !important; padding: 2rem !important;
}
[data-testid="stFileUploader"] label { color: #e5e7eb !important; }

/* Buttons */
.stButton > button {
    background: #C8F135 !important; color: #0a0a0f !important;
    font-weight: 700 !important; border: none !important;
    border-radius: 9px !important; padding: 9px 22px !important; font-size: 13px !important;
    transition: filter .15s ease !important;
}
.stButton > button:hover { filter: brightness(1.08) !important; }
.stDownloadButton > button {
    background: #14141c !important; color: #C8F135 !important;
    border: 1px solid #333f16 !important; font-weight: 600 !important;
    border-radius: 9px !important;
}

/* Expander */
[data-testid="stExpander"] { border: 1px solid #23232b !important; border-radius: 10px !important; background: #0d0d14 !important; }
[data-testid="stExpander"] summary { color: #b7b9c0 !important; font-size: 13px !important; }

/* KPI cards */
.kpi-card {
    background: #0d0d14; border: 1px solid #23232b; border-radius: 14px;
    padding: 24px 22px; height: 150px; display: flex; flex-direction: column; justify-content: center;
}
.kpi-value { font-size: 34px; font-weight: 800; color: #f3f4f6; line-height: 1; }
.kpi-label { font-size: 11px; color: #8b8b95; margin-top: 10px; text-transform: uppercase; letter-spacing: .08em; font-weight: 600; }
.kpi-sub   { font-size: 12px; color: #9ca3af; margin-top: 8px; }

/* Segment / summary cards */
.seg-card {
    background: #0d0d14; border: 1px solid #23232b; border-radius: 14px;
    padding: 22px; margin-bottom: 16px;
}
.seg-title { font-size: 18px; font-weight: 800; color: #f3f4f6; }
.seg-size  { font-size: 13px; color: #8b8b95; margin-top: 2px; }

/* Section headers */
.section-header {
    font-size: 15px; font-weight: 700; color: #f3f4f6;
    text-transform: uppercase; letter-spacing: .06em;
    margin: 34px 0 16px 0; display: flex; align-items: center; gap: 10px;
}
.section-header::before { content: ""; width: 3px; height: 15px; background: #C8F135; border-radius: 2px; display: inline-block; }

/* Story sections */
.story-section {
    background: #0d0d14; border: 1px solid #23232b; border-radius: 14px; padding: 30px 32px;
    margin-bottom: 22px;
}
.story-title { font-size: 19px; font-weight: 800; color: #f3f4f6; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; }
.story-body  { font-size: 15px; color: #c3c5cc; line-height: 1.9; }

/* Platform header */
.platform-header {
    padding: 20px 0 14px 0; border-bottom: 1px solid #1a1a22; margin-bottom: 20px;
}
.platform-name { font-size: 26px; font-weight: 800; color: #f3f4f6; letter-spacing: -0.5px; }
.platform-tag  { font-size: 13.5px; color: #8b8b95; margin-top: 6px; max-width: 820px; line-height: 1.55; }

/* Upload info grid */
.col-info {
    background: #0d0d14; border: 1px solid #23232b; border-radius: 10px;
    padding: 13px 16px; margin-bottom: 8px;
}
.col-name   { font-size: 13px; font-weight: 700; color: #C8F135; }
.col-unlock { font-size: 12px; color: #8b8b95; margin-top: 2px; }

/* Badges */
.fiq-badge { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: .02em; line-height: 1.5; white-space: nowrap; }

/* Custom dark tables */
.fiq-table-wrap { border: 1px solid #2a2a32; border-radius: 12px; overflow: hidden; margin: 6px 0 8px; }
.fiq-table { width: 100%; border-collapse: collapse; }
.fiq-table th { background: #2A2A2A; color: #C8F135; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; padding: 12px 16px; text-align: left; white-space: nowrap; }
.fiq-table td { padding: 11px 16px; font-size: 13px; color: #d1d5db; border: none; }
.fiq-table tbody tr:nth-child(odd) td { background: #1A1A1A; }
.fiq-table tbody tr:nth-child(even) td { background: #222222; }
</style>
""", unsafe_allow_html=True)


# ── UI kit ─────────────────────────────────────────────────────────────────
BADGE_COLORS = {
    "green": ("#14351f", "#7ee787"),
    "amber": ("#3a2c0d", "#f5c451"),
    "red":   ("#3a1618", "#f78186"),
    "blue":  ("#122540", "#6ea8fe"),
    "grey":  ("#26262e", "#a1a1aa"),
}


def badge(text, kind="grey"):
    bg, fg = BADGE_COLORS.get(kind, BADGE_COLORS["grey"])
    return f'<span class="fiq-badge" style="background:{bg};color:{fg};">{text}</span>'


def confidence_kind(v): return {"High": "green", "Medium": "amber", "Low": "red"}.get(str(v), "grey")
def effort_kind(v):     return {"Low": "green", "Medium": "amber", "High": "red"}.get(str(v), "grey")
def fit_kind(v):        return {"HIGH": "green", "MED": "amber", "LOW": "grey"}.get(str(v).upper(), "grey")
def attention_kind(v):  return {"Growing": "green", "Stable": "blue", "Watchlist": "amber", "Fading": "red"}.get(str(v), "grey")


def confidence_badge(v): return badge(v, confidence_kind(v))
def effort_badge(v):     return badge(v, effort_kind(v))
def fit_badge(v):        return badge(v, fit_kind(v))
def attention_badge(v):  return badge(v, attention_kind(v))


def trend_arrow_html(arrow):
    color = {"↑": "#7ee787", "→": "#a1a1aa", "↓": "#f78186"}.get(arrow, "#a1a1aa")
    return f'<span style="color:{color};font-weight:800;">{arrow}</span>'


def html_table(headers, rows):
    """Render a dark-themed table. Cells may contain HTML (e.g. badges)."""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return (f'<div class="fiq-table-wrap"><table class="fiq-table">'
            f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def kpi_card(value, label, sub_html="", accent="#f3f4f6", highlight=False):
    ring = "box-shadow:0 0 0 1px #C8F13544;border-color:#3a4718;" if highlight else ""
    sub = f'<div class="kpi-sub">{sub_html}</div>' if sub_html else ""
    return (f'<div class="kpi-card" style="{ring}">'
            f'<div class="kpi-value" style="color:{accent};">{value}</div>'
            f'<div class="kpi-label">{label}</div>{sub}</div>')

# ── Helpers ────────────────────────────────────────────────────────────────
TODAY = date(2026, 6, 28)

CORE_COLUMNS = {
    "Fan_ID":           "Required base for all features",
    "Age":              "Unlocks Fan Cohort Breakdown",
    "Gender":           "Unlocks Demographic Intelligence",
    "Last_Attended":    "Unlocks Loyalty Score and Churn Risk",
    "Tickets_Purchased":"Unlocks Commercial Behaviour Score",
    "Spend":            "Unlocks Revenue Intelligence and LTV",
    "Membership_Type":  "Unlocks Tier Analysis",
    "Engagement_Score": "Unlocks Engagement Index",
    "Channel_Preference":"Unlocks Campaign Intelligence tab",
    "Country":          "Unlocks Geographic Fan Analysis",
    "Favourite_Player": "Unlocks Player Influence tab (gated)",
}

COLUMN_ALIASES = {
    "Fan_ID":            ["fan_id","id","fan id","customer_id","member_id","supporter_id","fanid"],
    "Age":               ["age","age_years","years","dob","date_of_birth"],
    "Gender":            ["gender","sex","gender_identity"],
    "Last_Attended":     ["last_attended","last_visit","last_match","last_game","last_event","last attendance"],
    "Tickets_Purchased": ["tickets_purchased","tickets","ticket_count","num_tickets","tickets purchased"],
    "Spend":             ["spend","total_spend","revenue","total_revenue","amount","spend_total"],
    "Membership_Type":   ["membership_type","membership","tier","member_tier","membership type"],
    "Engagement_Score":  ["engagement_score","engagement","eng_score","engagement score"],
    "Channel_Preference":["channel_preference","channel","preferred_channel","comms_channel"],
    "Country":           ["country","nation","region","location","nationality"],
    "Favourite_Player":  ["favourite_player","favorite_player","fav_player","player","preferred_player"],
}

SEGMENT_COLORS = {
    "VIP":            "#C8F135",  # Primary
    "High Potential": "#3B82F6",  # Secondary
    "Regular":        "#8B5CF6",  # Tertiary
    "Win Back":       "#EF4444",  # Negative
    "Dormant":        "#6B7280",  # Neutral
}


def _pdf_safe(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "…": "...", "£": "GBP",
        "€": "EUR", "±": "+/-", "×": "x", "•": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def fuzzy_map_columns(df: pd.DataFrame) -> dict:
    """Map uploaded column names to canonical FanIQ column names using fuzzy matching."""
    try:
        from rapidfuzz import fuzz
        use_rapidfuzz = True
    except ImportError:
        use_rapidfuzz = False

    mapping = {}
    df_cols_lower = {c.lower().strip().replace(" ", "_"): c for c in df.columns}

    for canonical, aliases in COLUMN_ALIASES.items():
        best_col = None
        best_score = 0
        for alias in aliases:
            alias_norm = alias.lower().replace(" ", "_")
            if alias_norm in df_cols_lower:
                best_col = df_cols_lower[alias_norm]
                best_score = 100
                break
            if use_rapidfuzz:
                for col_norm, col_orig in df_cols_lower.items():
                    score = fuzz.ratio(alias_norm, col_norm)
                    if score > best_score and score >= 75:
                        best_score = score
                        best_col = col_orig
        if best_col:
            mapping[canonical] = best_col
    return mapping


def remap_df(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Return a copy of df with columns renamed to canonical names."""
    inv = {v: k for k, v in mapping.items()}
    df2 = df.rename(columns=inv)
    return df2


# ── Scoring Engine ─────────────────────────────────────────────────────────
MEMBERSHIP_RANK = {
    "none": 0, "bronze": 1, "associate": 1, "silver": 2, "full member": 2,
    "gold": 3, "life member": 3, "platinum": 4, "surrey & england": 4,
    "vip": 4, "premium": 3,
}


def _days_since(series: pd.Series) -> pd.Series:
    today = pd.Timestamp(TODAY)
    parsed = pd.to_datetime(series, errors="coerce")
    diff = (today - parsed).dt.days.fillna(730)
    return diff


def _pct_rank(series: pd.Series) -> pd.Series:
    return series.rank(pct=True) * 100


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    cols = set(df.columns)

    # ── Engagement Score ──
    if "Engagement_Score" in cols:
        raw_eng = pd.to_numeric(df["Engagement_Score"], errors="coerce").fillna(50)
    else:
        raw_eng = pd.Series(np.random.default_rng(1).uniform(20, 80, n), index=df.index)
    if "Last_Attended" in cols:
        days_att = _days_since(df["Last_Attended"])
        recency_bonus = np.clip(100 - days_att / 10, 0, 100)
        raw_eng = raw_eng * 0.6 + recency_bonus * 0.4
    df["Engagement_Score_Raw"] = raw_eng
    df["Engagement_Score_Pct"] = _pct_rank(raw_eng).round(1)

    # ── Commercial Score ──
    raw_comm = pd.Series(np.zeros(n), index=df.index)
    if "Spend" in cols:
        spend = pd.to_numeric(df["Spend"], errors="coerce").fillna(0)
        raw_comm += _pct_rank(spend) * 0.5
    if "Tickets_Purchased" in cols:
        tix = pd.to_numeric(df["Tickets_Purchased"], errors="coerce").fillna(0)
        raw_comm += _pct_rank(tix) * 0.3
    if "Membership_Type" in cols:
        mem_rank = df["Membership_Type"].str.lower().str.strip().map(
            lambda x: MEMBERSHIP_RANK.get(x, 0)
        )
        raw_comm += (mem_rank / 4 * 100) * 0.2
    if raw_comm.sum() == 0:
        raw_comm = pd.Series(np.random.default_rng(2).uniform(20, 80, n), index=df.index)
    df["Commercial_Score"] = _pct_rank(raw_comm).round(1)

    # ── Loyalty Score ──
    raw_loy = pd.Series(np.zeros(n), index=df.index)
    if "Last_Attended" in cols:
        days_att = _days_since(df["Last_Attended"])
        raw_loy += np.clip(100 - days_att / 5, 0, 100) * 0.5
    if "Membership_Type" in cols:
        mem_rank = df["Membership_Type"].str.lower().str.strip().map(
            lambda x: MEMBERSHIP_RANK.get(x, 0)
        )
        raw_loy += (mem_rank / 4 * 100) * 0.3
    if "Tickets_Purchased" in cols:
        tix = pd.to_numeric(df["Tickets_Purchased"], errors="coerce").fillna(0)
        raw_loy += _pct_rank(tix) * 0.2
    if raw_loy.sum() == 0:
        raw_loy = pd.Series(np.random.default_rng(3).uniform(20, 80, n), index=df.index)
    df["Loyalty_Score"] = _pct_rank(raw_loy).round(1)

    # ── Churn Risk Index (lower = better) ──
    raw_churn = pd.Series(np.zeros(n), index=df.index)
    if "Last_Attended" in cols:
        days_att = _days_since(df["Last_Attended"])
        raw_churn += np.clip(days_att / 10, 0, 100) * 0.5
    if "Engagement_Score" in cols:
        raw_eng2 = pd.to_numeric(df["Engagement_Score"], errors="coerce").fillna(50)
        raw_churn += (100 - _pct_rank(raw_eng2)) * 0.3
    if "Spend" in cols:
        spend = pd.to_numeric(df["Spend"], errors="coerce").fillna(0)
        raw_churn += (100 - _pct_rank(spend)) * 0.2
    if raw_churn.sum() == 0:
        raw_churn = pd.Series(np.random.default_rng(4).uniform(20, 80, n), index=df.index)
    df["Churn_Risk"] = _pct_rank(raw_churn).round(1)

    # ── Conversion Probability ──
    raw_conv = pd.Series(np.zeros(n), index=df.index)
    raw_conv += df["Engagement_Score_Pct"] * 0.4
    raw_conv += df["Commercial_Score"] * 0.3
    raw_conv += (100 - df["Churn_Risk"]) * 0.3
    df["Conversion_Probability"] = _pct_rank(raw_conv).round(1)

    # ── LTV Estimate ──
    if "Spend" in cols:
        spend = pd.to_numeric(df["Spend"], errors="coerce").fillna(0)
        df["LTV_Estimate"] = (spend * (df["Loyalty_Score"] / 50 + 1)).round(2)
    else:
        df["LTV_Estimate"] = (df["Commercial_Score"] * 20).round(2)

    # ── Segment Assignment ──
    def assign_segment(row):
        if row["Commercial_Score"] >= 75 and row["Engagement_Score_Pct"] >= 70:
            return "VIP"
        elif row["Commercial_Score"] >= 55 or row["Engagement_Score_Pct"] >= 60:
            return "High Potential"
        elif row["Churn_Risk"] >= 70:
            if row["Commercial_Score"] >= 30:
                return "Win Back"
            return "Dormant"
        else:
            return "Regular"

    df["Segment"] = df.apply(assign_segment, axis=1)

    # ── Journey Stage ──
    def journey_stage(row):
        score = (row["Engagement_Score_Pct"] + row["Commercial_Score"] + row["Loyalty_Score"]) / 3
        if score >= 80:   return 5
        elif score >= 65: return 4
        elif score >= 50: return 3
        elif score >= 35: return 2
        else:             return 1

    df["Journey_Stage"] = df.apply(journey_stage, axis=1)

    df = compute_faqi(df)

    return df


# ── FAQI: Fan Attention Quality Index ──────────────────────────────────────
ATTENTION_COLORS = {
    "Growing":   "#C8F135",  # Primary
    "Stable":    "#3B82F6",  # Secondary
    "Watchlist": "#8B5CF6",  # Tertiary
    "Fading":    "#EF4444",  # Negative
}

FAQI_COMPONENTS = [
    ("FAQI_Trend",      "Engagement Trend",    0.30),
    ("FAQI_Channel",    "Channel Consistency", 0.20),
    ("FAQI_Recency",    "Recency",             0.25),
    ("FAQI_Commercial", "Commercial Weight",   0.15),
    ("FAQI_Breadth",    "Format Breadth",      0.10),
]

# Plain-language driver phrasing per component (positive, negative)
FAQI_DRIVER_TEXT = {
    "FAQI_Trend":      ("Engagement rising versus the cohort",        "Engagement below the cohort average"),
    "FAQI_Channel":    ("Clear contact channel on file",              "Channel preference unknown"),
    "FAQI_Recency":    ("Attended recently",                          "Long time since last attended"),
    "FAQI_Commercial": ("Strong spend for engagement level",          "Retail spend below cohort average"),
    "FAQI_Breadth":    ("Active across membership, tickets and spend", "Engages through a single format only"),
}

ATTENTION_MEANING = {
    "Growing":   "attention is expanding, capitalise now.",
    "Stable":    "attention is steady, nurture the relationship.",
    "Watchlist": "attention is slipping, intervene soon.",
    "Fading":    "attention is contracting, act urgently.",
}


def attention_status(faqi: float) -> str:
    if faqi >= 71: return "Growing"
    if faqi >= 51: return "Stable"
    if faqi >= 31: return "Watchlist"
    return "Fading"


def compute_faqi(df: pd.DataFrame) -> pd.DataFrame:
    """Fan Attention Quality Index (0-100). Missing columns fall back to sensible defaults."""
    n = len(df)
    idx = df.index
    cols = set(df.columns)

    eng = (pd.to_numeric(df["Engagement_Score"], errors="coerce").fillna(50)
           if "Engagement_Score" in cols else pd.Series(50.0, index=idx))
    tickets = (pd.to_numeric(df["Tickets_Purchased"], errors="coerce").fillna(0)
               if "Tickets_Purchased" in cols else pd.Series(0.0, index=idx))
    spend = (pd.to_numeric(df["Spend"], errors="coerce").fillna(0)
             if "Spend" in cols else pd.Series(0.0, index=idx))
    membership = (df["Membership_Type"].astype(str)
                  if "Membership_Type" in cols else pd.Series("None", index=idx))
    channel = (df["Channel_Preference"]
               if "Channel_Preference" in cols else pd.Series([None] * n, index=idx))

    if "Last_Attended" in cols:
        parsed = pd.to_datetime(df["Last_Attended"], errors="coerce")
        days = (pd.Timestamp(TODAY) - parsed).dt.days
    else:
        days = pd.Series(np.nan, index=idx)
    days_null = days.isna()

    # 1. Engagement Trend (30%)
    eng_avg = eng.mean()
    above_avg = eng > eng_avg
    trend = (50 + (eng - eng_avg)).clip(0, 100)
    trend = trend.where(~(above_avg & (tickets > 0)), other=trend.clip(lower=80))
    low_mask = (~above_avg) & (days.fillna(999) > 180)
    trend = trend.where(~low_mask, other=trend.clip(upper=20))
    df["FAQI_Trend"] = trend.round(1)

    # 2. Channel Consistency (20%)
    ch_str = channel.astype(str).str.strip().str.lower()
    ch_valid = channel.notna() & (~ch_str.isin(["", "unknown", "nan", "none"]))
    df["FAQI_Channel"] = np.where(ch_valid, 75.0, 25.0)

    # 3. Recency Decay (25%)
    recency = pd.Series(10.0, index=idx)
    recency = recency.mask(days < 365, 40.0)
    recency = recency.mask(days < 180, 70.0)
    recency = recency.mask(days < 90, 100.0)
    recency = recency.mask(days_null, 10.0)
    df["FAQI_Recency"] = recency

    # 4. Commercial Weight (15%)
    cw_raw = ((spend / (eng + 1)) * 100).clip(upper=100)
    cw_avg = cw_raw.mean()
    df["FAQI_Commercial"] = np.where(cw_raw > cw_avg, 75.0, 35.0)

    # 5. Format Breadth (10%)
    has_mem = membership.str.strip().str.lower() != "none"
    breadth_count = has_mem.astype(int) + (tickets > 0).astype(int) + (spend > 0).astype(int)
    df["FAQI_Breadth"] = breadth_count.map({3: 100.0, 2: 65.0, 1: 35.0, 0: 10.0})

    faqi = (df["FAQI_Trend"] * 0.30 + df["FAQI_Channel"] * 0.20 +
            df["FAQI_Recency"] * 0.25 + df["FAQI_Commercial"] * 0.15 +
            df["FAQI_Breadth"] * 0.10)
    df["FAQI"] = faqi.clip(0, 100).round(1)
    df["Attention_Status"] = df["FAQI"].apply(attention_status)

    faqi_avg = df["FAQI"].mean()
    diff = df["FAQI"] - faqi_avg
    df["Attention_Trend"] = np.where(diff.abs() <= 5, "→", np.where(diff > 5, "↑", "↓"))

    return df


def faqi_driver_breakdown(component_scores: dict):
    """Return (positives, negatives) plain-language lists from a component-score dict."""
    ranked = sorted(component_scores.items(), key=lambda kv: kv[1], reverse=True)
    positives, negatives = [], []
    for key, val in ranked[:2]:
        if val >= 55:
            positives.append(FAQI_DRIVER_TEXT[key][0])
    for key, val in reversed(ranked):
        if val <= 50 and len(negatives) < 2:
            negatives.append(FAQI_DRIVER_TEXT[key][1])
    if not positives:
        positives.append(FAQI_DRIVER_TEXT[ranked[0][0]][0])
    if not negatives:
        negatives.append(FAQI_DRIVER_TEXT[ranked[-1][0]][1])
    return positives, negatives


def segment_faqi_summary(df: pd.DataFrame, segment: str):
    seg = df[df["Segment"] == segment]
    if not len(seg):
        return None
    comp = {k: float(seg[k].mean()) for k, _, _ in FAQI_COMPONENTS}
    avg = float(seg["FAQI"].mean())
    pos, neg = faqi_driver_breakdown(comp)
    return {"avg": avg, "status": attention_status(avg), "pos": pos, "neg": neg}


# ── Commercial intelligence helpers ────────────────────────────────────────
CORE_FOR_COMPLETENESS = [
    "Fan_ID", "Age", "Gender", "Last_Attended", "Tickets_Purchased",
    "Spend", "Membership_Type", "Engagement_Score", "Channel_Preference",
]

# Per-segment action economics for the Commercial Outlook
OPPORTUNITY_META = {
    "VIP":            {"action": "Protect and upsell VIP fans",            "effort": "Low",    "tti": "2-4 weeks",  "recovery": 0.06},
    "High Potential": {"action": "Convert High Potential fans to members", "effort": "Medium", "tti": "4-8 weeks",  "recovery": 0.25},
    "Regular":        {"action": "Increase Regular fan visit frequency",   "effort": "Low",    "tti": "2-3 weeks",  "recovery": 0.15},
    "Win Back":       {"action": "Reactivate Win Back fans",               "effort": "Medium", "tti": "3-6 weeks",  "recovery": 0.10},
    "Dormant":        {"action": "Low-cost Dormant reactivation",          "effort": "High",   "tti": "6-12 weeks", "recovery": 0.05},
}

CHANNEL_COST = {"email": 0.10, "sms": 0.25, "push": 0.05, "social": 0.15, "direct mail": 1.50}

# Offer/incentive cost as a share of revenue generated (discounts, free tickets,
# hospitality). Used with per-contact cost to give a realistic campaign ROI.
OFFER_COST_RATIO = {
    "VIP": 0.35, "High Potential": 0.25, "Regular": 0.30,
    "Win Back": 0.40, "Dormant": 0.55,
}


def data_completeness(df: pd.DataFrame) -> float:
    present = sum(1 for c in CORE_FOR_COMPLETENESS if c in df.columns)
    return present / len(CORE_FOR_COMPLETENESS)


def confidence_score(df: pd.DataFrame, size: int):
    """Return (label, pct) from segment size and data completeness."""
    total = len(df)
    comp = data_completeness(df)
    frac = (size / total) if total else 0
    score = comp * 0.6 + min(frac / 0.15, 1.0) * 0.4
    pct = int(round(score * 100))
    if score >= 0.66: return "High", pct
    if score >= 0.40: return "Medium", pct
    return "Low", pct


def segment_avg_value(df: pd.DataFrame, segment: str) -> float:
    """Average per-fan commercial value for a segment. Falls back through segment LTV
    then fanbase averages so revenue cards never collapse to zero."""
    seg = df[df["Segment"] == segment]
    if not len(seg):
        return 0.0
    val = 0.0
    if "Spend" in df.columns:
        val = float(pd.to_numeric(seg["Spend"], errors="coerce").fillna(0).mean())
    if val <= 0:
        val = float(seg["LTV_Estimate"].mean())
    if val <= 0:
        # segment value near zero — fall back to fanbase averages
        if "Spend" in df.columns:
            val = float(pd.to_numeric(df["Spend"], errors="coerce").fillna(0).mean())
        if val <= 0:
            val = float(df["LTV_Estimate"].mean())
    return max(val, 1.0)


def channel_cost(channel: str) -> float:
    c = str(channel).lower()
    for key, cost in CHANNEL_COST.items():
        if key in c:
            return cost
    return 0.20


def compute_pitch_score(df: pd.DataFrame) -> float:
    cols = set(df.columns)
    pitch = 58
    pitch += (df["Commercial_Score"].mean() - 50) * 0.3
    if "Age" in cols:
        core_demo = ((df["Age"] >= 18) & (df["Age"] <= 35)).sum() / len(df) * 100
        pitch += (core_demo - 30) * 0.2
    if "Gender" in cols:
        female_pct = (df["Gender"].str.lower() == "female").sum() / len(df) * 100
        pitch += (female_pct - 25) * 0.15
    return round(float(np.clip(pitch, 0, 100)), 1)


def get_top_sponsor(df: pd.DataFrame) -> dict:
    """Top sponsor category fit with a strategic fit rating (0-100)."""
    pitch = compute_pitch_score(df)
    category, fit, brands, why = SPONSOR_CATEGORIES[0]
    base = {"HIGH": 85, "MED": 68, "LOW": 52}.get(fit, 60)
    rating = int(round(min(97, base + (pitch - 58) * 0.3)))
    return {"category": category, "fit": fit, "brands": brands, "why": why, "rating": rating}


def build_opportunities(df: pd.DataFrame) -> list:
    seg_counts = df["Segment"].value_counts()
    opps = []
    for seg, meta in OPPORTUNITY_META.items():
        size = int(seg_counts.get(seg, 0))
        if size == 0:
            continue
        avg_val = segment_avg_value(df, seg)
        est_rev = size * avg_val * meta["recovery"]
        conf_label, conf_pct = confidence_score(df, size)
        opps.append({
            "segment": seg, "action": meta["action"], "est_revenue": est_rev,
            "confidence": conf_label, "confidence_pct": conf_pct,
            "effort": meta["effort"], "tti": meta["tti"],
        })
    return opps


def biggest_risk(df: pd.DataFrame):
    """Return (segment, ltv_at_risk) for the segment with the highest average churn risk.
    Uses a fanbase-average fallback so the value never collapses to zero."""
    seg_churn = df.groupby("Segment")["Churn_Risk"].mean()
    risk_seg = seg_churn.idxmax()
    seg = df[df["Segment"] == risk_seg]
    churn_factor = float(seg["Churn_Risk"].mean() / 100)
    at_risk = float(seg["LTV_Estimate"].sum()) * churn_factor
    if at_risk < 1:
        at_risk = len(seg) * segment_avg_value(df, risk_seg) * churn_factor
    return risk_seg, max(at_risk, 1.0)


def has_player_data(df: pd.DataFrame) -> bool:
    """True only if Favourite_Player exists and has real values (not empty / all Unknown)."""
    if "Favourite_Player" not in df.columns:
        return False
    s = df["Favourite_Player"].astype(str).str.strip().str.lower()
    valid = s[~s.isin(["", "unknown", "nan", "none"])]
    return len(valid) > 0


def generate_executive_brief_pdf(df: pd.DataFrame) -> bytes:
    opps = sorted(build_opportunities(df), key=lambda o: o["est_revenue"], reverse=True)
    risk_seg, ltv_at_risk = biggest_risk(df)
    sponsor = get_top_sponsor(df)
    total_ltv = df["LTV_Estimate"].sum()
    avg_faqi = df["FAQI"].mean()
    top_seg = df["Segment"].value_counts().index[0]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Light header band
    pdf.set_fill_color(200, 241, 53)  # #C8F135
    pdf.rect(0, 0, 210, 26, "F")
    pdf.set_xy(10, 7)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(8, 8, 16)
    pdf.cell(0, 12, _pdf_safe("FanIQ Executive Brief"), ln=True)
    pdf.set_xy(10, 30)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, _pdf_safe(f"Generated {TODAY.strftime('%d %B %Y')}"), ln=True)
    pdf.ln(6)

    def section(title):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 9, _pdf_safe(title), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)

    section("Fanbase Snapshot")
    for label, val in [
        ("Total fans", f"{len(df):,}"),
        ("Average FAQI", f"{avg_faqi:.0f} ({attention_status(avg_faqi)})"),
        ("Top segment", str(top_seg)),
        ("Total estimated LTV", f"GBP {total_ltv:,.0f}"),
    ]:
        pdf.cell(65, 6, _pdf_safe(label + ":"), border=0)
        pdf.cell(0, 6, _pdf_safe(val), ln=True)
    pdf.ln(4)

    section("Top 3 Commercial Opportunities")
    for o in opps[:3]:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(20, 20, 20)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, _pdf_safe(
            f"{o['action']} - GBP {o['est_revenue']:,.0f} "
            f"({o['confidence']} confidence, {o['effort']} effort)"))
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
    pdf.ln(2)

    section("Biggest Commercial Risk")
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, _pdf_safe(
        f"{risk_seg} segment - an estimated GBP {ltv_at_risk:,.0f} in lifetime "
        f"value is at risk if no action is taken."))
    pdf.ln(2)

    section("Sponsor Opportunity")
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, _pdf_safe(
        f"{sponsor['category']} ({sponsor['rating']}% strategic fit) - {sponsor['why']}"))
    pdf.ln(2)

    section("Recommended Actions - Next 7 Days")
    for o in opps[:3]:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, _pdf_safe(f"- {o['action']} (est. GBP {o['est_revenue']:,.0f})"))
    pdf.ln(8)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, _pdf_safe("Generated by FanIQ"), ln=True)
    return bytes(pdf.output())


# ── Commercial Outlook (default landing page) ──────────────────────────────
def render_commercial_outlook(df: pd.DataFrame):
    opps = build_opportunities(df)
    if not opps:
        st.info("Not enough segmented data to build a commercial outlook.")
        return
    opps_sorted = sorted(opps, key=lambda o: o["est_revenue"], reverse=True)
    biggest = opps_sorted[0]
    priority = opps_sorted[:3]
    combined = sum(o["est_revenue"] for o in priority)
    risk_seg, ltv_at_risk = biggest_risk(df)
    low_effort = [o for o in opps if o["effort"] == "Low"]
    quick = max(low_effort or opps, key=lambda o: o["confidence_pct"])
    sponsor = get_top_sponsor(df)

    # Top-line summary
    st.markdown(
        f'<div style="font-size:12px;color:#8b8b95;font-weight:700;letter-spacing:.09em;'
        f'text-transform:uppercase;margin-bottom:10px;">This Week</div>'
        f'<div style="font-size:23px;font-weight:800;color:#f3f4f6;line-height:1.45;max-width:920px;">'
        f'Your fanbase has <span style="color:#C8F135;">{len(priority)} high-priority '
        f'{"opportunity" if len(priority)==1 else "opportunities"}</span>, worth an estimated '
        f'<span style="color:#C8F135;">+&pound;{combined:,.0f}</span> in recoverable revenue upside.</div>',
        unsafe_allow_html=True)
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # Four summary cards — revenue is the hero element, meta is secondary
    def _card(label, name, hero, accent, meta_html):
        return (f'<div style="background:#0d0d14;border:1px solid #23232b;border-top:3px solid {accent};'
                f'border-radius:14px;padding:22px 22px 20px;height:238px;display:flex;flex-direction:column;">'
                f'<div style="font-size:10.5px;color:#8b8b95;text-transform:uppercase;letter-spacing:.09em;font-weight:700;">{label}</div>'
                f'<div style="font-size:17px;font-weight:800;color:{accent};margin-top:12px;">{name}</div>'
                f'<div style="font-size:30px;font-weight:800;color:#f3f4f6;margin-top:auto;line-height:1.05;">{hero}</div>'
                f'<div style="margin-top:13px;">{meta_html}</div></div>')

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        meta = (f'{confidence_badge(biggest["confidence"])} &nbsp; {effort_badge(biggest["effort"])}'
                f'<div style="font-size:11.5px;color:#8b8b95;margin-top:10px;">Recoverable upside &middot; {biggest["tti"]} to impact</div>')
        st.markdown(_card("Biggest Opportunity", biggest["segment"], f"+&pound;{biggest['est_revenue']:,.0f}", "#C8F135", meta), unsafe_allow_html=True)
    with c2:
        meta = '<div style="font-size:11.5px;color:#8b8b95;margin-top:10px;">Lifetime value at risk if no action is taken</div>'
        st.markdown(_card("Biggest Risk", risk_seg, f"&pound;{ltv_at_risk:,.0f}", "#EF4444", meta), unsafe_allow_html=True)
    with c3:
        meta = (f'{confidence_badge(quick["confidence"])} &nbsp; {effort_badge(quick["effort"])}'
                f'<div style="font-size:11.5px;color:#8b8b95;margin-top:10px;">Recoverable upside &middot; fastest high-confidence action</div>')
        st.markdown(_card("Quick Win", quick["segment"], f"+&pound;{quick['est_revenue']:,.0f}", "#3B82F6", meta), unsafe_allow_html=True)
    with c4:
        meta = (f'{fit_badge(sponsor["fit"])}'
                f'<div style="font-size:11.5px;color:#8b8b95;margin-top:10px;">Strategic fit rating</div>')
        st.markdown(_card("Sponsor Opportunity", sponsor["category"], f"{sponsor['rating']}%", "#8B5CF6", meta), unsafe_allow_html=True)

    # Prioritised opportunities table (dark, badge-enabled)
    st.markdown('<div class="section-header">Prioritised Opportunities</div>', unsafe_allow_html=True)
    rows = [[
        f'<span style="color:#e5e7eb;font-weight:600;">{o["action"]}</span>',
        f'<span style="color:#C8F135;font-weight:700;">+&pound;{o["est_revenue"]:,.0f}</span>',
        confidence_badge(o["confidence"]),
        effort_badge(o["effort"]),
        o["tti"],
    ] for o in opps_sorted[:5]]
    st.markdown(html_table(["Opportunity", "Revenue Upside", "Confidence", "Effort", "Time to Impact"], rows),
                unsafe_allow_html=True)

    # Recommended action — executive conclusion of the page
    channel = get_channel_for_segment(df, biggest["segment"])
    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:linear-gradient(180deg,#141a08,#0d0d14);border:1px solid #333f16;
                border-left:4px solid #C8F135;border-radius:14px;padding:28px 30px;">
        <div style="font-size:11px;color:#C8F135;text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-bottom:14px;">Recommended Action This Week</div>
        <div style="font-size:24px;font-weight:800;color:#f3f4f6;line-height:1.35;">Launch a targeted {biggest['segment']} campaign via {channel}.</div>
        <div style="display:flex;align-items:center;gap:18px;margin:18px 0 14px;flex-wrap:wrap;">
            <div style="font-size:28px;font-weight:800;color:#C8F135;">+&pound;{biggest['est_revenue']:,.0f} <span style="font-size:13px;font-weight:600;color:#8b8b95;">upside</span></div>
            <div>{confidence_badge(biggest['confidence'])}</div>
        </div>
        <div style="font-size:14px;color:#9ca3af;line-height:1.65;max-width:780px;">The single highest-return action available this week, based on segment value, conversion likelihood and the effort required to execute.</div>
    </div>""", unsafe_allow_html=True)


# ── Upload Screen ──────────────────────────────────────────────────────────
def render_upload_screen():
    st.markdown("""
    <div class="platform-header">
        <div class="platform-name">⚡ FanIQ</div>
        <div class="platform-tag">FanIQ helps sports organisations identify, prioritise and act on their highest-value commercial opportunities using fan intelligence.</div>
    </div>
    """, unsafe_allow_html=True)

    col_up, col_info = st.columns([3, 2], gap="large")

    with col_up:
        st.markdown('<div class="section-header">Upload Your Fan Database</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#888;font-size:13px;">Any CSV format. FanIQ auto-detects columns, no template required.</p>', unsafe_allow_html=True)

        uploaded = st.file_uploader("Drop your CSV here or click to browse", type=["csv"], label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)

        with c1:
            sample_df = generate_sample_data(300)
            csv_sample = sample_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Sample CSV (300 fans)", csv_sample, "faniq_sample.csv", "text/csv")

        with c2:
            template_df = generate_template()
            csv_tmpl = template_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ CSV Template (headers)", csv_tmpl, "faniq_template.csv", "text/csv")

        with c3:
            if st.button("▶ Load Sample Data"):
                st.session_state["df_raw"] = sample_df
                st.session_state["df"] = None
                st.rerun()

        if uploaded:
            try:
                raw = pd.read_csv(uploaded)
                st.session_state["df_raw"] = raw
                st.session_state["df"] = None
                st.success(f"Loaded {len(raw):,} fans · {len(raw.columns)} columns")
                st.rerun()
            except Exception as e:
                st.error(f"Could not parse CSV: {e}")

    with col_info:
        st.markdown('<div class="section-header">Recommended Columns</div>', unsafe_allow_html=True)
        for col, unlock in CORE_COLUMNS.items():
            req = " ★" if col == "Fan_ID" else ""
            st.markdown(f"""
            <div class="col-info">
                <div class="col-name">{col}{req}</div>
                <div class="col-unlock">{unlock}</div>
            </div>
            """, unsafe_allow_html=True)


# ── Tab 1: Fan Dashboard ───────────────────────────────────────────────────
def render_fan_dashboard(df: pd.DataFrame):
    seg_counts = df["Segment"].value_counts()
    high_churn = (df["Churn_Risk"] >= 70).sum()
    top_seg = seg_counts.index[0] if len(seg_counts) else "N/A"

    # KPI cards
    avg_faqi = df["FAQI"].mean()
    faqi_status = attention_status(avg_faqi)
    avg_comm = df["Commercial_Score"].mean()
    top_count = seg_counts.iloc[0] if len(seg_counts) else 0
    fq_color = ATTENTION_COLORS[faqi_status]
    k1, k2, k3, k4, k5 = st.columns(5, gap="medium")
    with k1:
        st.markdown(kpi_card(f"{len(df):,}", "Total Fans"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card(f"{avg_comm:.0f}", "Avg Commercial Score", "0-100 percentile"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card(f"{high_churn:,}", "Fans at Churn Risk", "Churn score 70+ across all segments"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card(f"{top_count:,}", "Top Segment", str(top_seg)), unsafe_allow_html=True)
    with k5:
        # FAQI is a proprietary metric — visually distinct with a ring + status badge beside the score
        st.markdown(
            f'<div class="kpi-card" style="box-shadow:0 0 0 1px #C8F13544;border-color:#3a4718;">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<div class="kpi-value" style="color:{fq_color};">{avg_faqi:.0f}</div>'
            f'{attention_badge(faqi_status)}</div>'
            f'<div class="kpi-label">Average FAQI &middot; Proprietary</div></div>',
            unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # FAQI intelligence layer
    st.markdown('<div class="section-header">Fan Attention (FAQI)</div>', unsafe_allow_html=True)
    fq1, fq2 = st.columns([3, 2])
    with fq1:
        status_order = ["Growing", "Stable", "Watchlist", "Fading"]
        status_counts = df["Attention_Status"].value_counts()
        counts = [int(status_counts.get(s, 0)) for s in status_order]
        fig_faqi = go.Figure(go.Bar(
            x=status_order, y=counts, text=counts, textposition="outside",
            marker_color=[ATTENTION_COLORS[s] for s in status_order], marker_line_width=0,
        ))
        fig_faqi.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#fff", height=240, margin=dict(t=10, b=30, l=40, r=10),
            showlegend=False, title="Fans by Attention Status", title_font_size=13,
        )
        st.plotly_chart(fig_faqi, use_container_width=True, key="dash_faqi_dist")
        comp_avg = {k: float(df[k].mean()) for k, _, _ in FAQI_COMPONENTS}
        pos, neg = faqi_driver_breakdown(comp_avg)
        with st.expander("What drives this score"):
            st.markdown("**Top contributors**")
            for p in pos:
                st.markdown(f"- ▲ {p}")
            for nneg in neg:
                st.markdown(f"- ▼ {nneg}")
            st.markdown("**Component breakdown** (each scored 0-100, then weighted)")
            comp_rows = [[name, f"{int(w * 100)}%", f"{comp_avg[k]:.0f}"] for k, name, w in FAQI_COMPONENTS]
            st.markdown(html_table(["Component", "Weight", "Avg Score"], comp_rows), unsafe_allow_html=True)
    with fq2:
        seg_faqi = df.groupby("Segment").agg(
            Fans=("Segment", "count"), Avg_FAQI=("FAQI", "mean"),
        ).round(1).reset_index()
        seg_faqi["Status"] = seg_faqi["Avg_FAQI"].apply(attention_status)
        seg_faqi = seg_faqi.sort_values("Avg_FAQI", ascending=False)
        st.markdown('<div style="font-size:12px;color:#8b8b95;margin-bottom:10px;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Attention by Segment</div>', unsafe_allow_html=True)
        rows = [[
            f'<span style="color:#e5e7eb;font-weight:600;">{r.Segment}</span>',
            f'{int(r.Fans):,}', f'{r.Avg_FAQI:.0f}', attention_badge(r.Status),
        ] for r in seg_faqi.itertuples()]
        st.markdown(html_table(["Segment", "Fans", "Avg FAQI", "Status"], rows), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 1: Segment donut + Journey funnel
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">Fan Segments</div>', unsafe_allow_html=True)
        seg_df = seg_counts.reset_index()
        seg_df.columns = ["Segment", "Count"]
        colors = [SEGMENT_COLORS.get(s, "#888") for s in seg_df["Segment"]]
        fig = go.Figure(go.Pie(
            labels=seg_df["Segment"], values=seg_df["Count"],
            hole=0.55, marker_colors=colors,
            textinfo="label+percent", textfont_color="#fff",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#fff", showlegend=False, margin=dict(t=20, b=20, l=20, r=20),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True, key="dash_donut")

    with c2:
        st.markdown('<div class="section-header">Fan Journey Funnel</div>', unsafe_allow_html=True)
        stage_labels = {1: "Awareness", 2: "Casual", 3: "Regular", 4: "Committed", 5: "Advocate"}
        total_fans = len(df)
        # Cumulative funnel: fans who have reached AT LEAST each stage. This is monotonic and
        # the first value equals the fanbase size, so "percent" can never divide by zero (no Infinity%).
        cum_counts = [int((df["Journey_Stage"] >= i).sum()) for i in range(1, 6)]
        stages = [stage_labels[i] for i in range(1, 6)]
        pct_labels = [f"{(c / total_fans * 100):.0f}%" if total_fans else "0%" for c in cum_counts]
        fig2 = go.Figure(go.Funnel(
            y=stages, x=cum_counts,
            text=pct_labels, textinfo="value+text",
            marker_color=["#6B7280", "#8B5CF6", "#3B82F6", "#9FC93B", "#C8F135"],
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#fff", margin=dict(t=20, b=20, l=120, r=20), height=320,
        )
        st.plotly_chart(fig2, use_container_width=True, key="dash_funnel")
        st.caption("Share of fans who have reached at least each journey stage (cumulative).")

    # Row 2: Score distributions
    st.markdown('<div class="section-header">Score Distributions</div>', unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    score_cols = [
        ("Engagement_Score_Pct", "Engagement", "#C8F135", s1, "dash_eng"),    # Primary
        ("Commercial_Score", "Commercial", "#3B82F6", s2, "dash_comm"),       # Secondary
        ("Loyalty_Score", "Loyalty", "#8B5CF6", s3, "dash_loy"),              # Tertiary
        ("Churn_Risk", "Churn Risk", "#EF4444", s4, "dash_churn"),            # Negative
        ("Conversion_Probability", "Conversion", "#C8F135", s5, "dash_conv"), # Primary
    ]
    for col, label, color, container, key in score_cols:
        with container:
            fig = px.histogram(df, x=col, nbins=20,
                               labels={col: label}, color_discrete_sequence=[color])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#fff", margin=dict(t=30, b=30, l=20, r=10),
                height=180, title=label, title_font_size=13,
                showlegend=False, xaxis=dict(range=[0, 100]),
            )
            fig.update_yaxes(showticklabels=False, title="")
            st.plotly_chart(fig, use_container_width=True, key=key)

    # Row 3: LTV distribution
    st.markdown('<div class="section-header">Fan LTV Distribution</div>', unsafe_allow_html=True)
    p95 = float(df["LTV_Estimate"].quantile(0.95))
    max_ltv = float(df["LTV_Estimate"].max())
    n_outliers = int((df["LTV_Estimate"] > p95).sum())
    fig_ltv = px.histogram(df, x="LTV_Estimate", nbins=40,
                           color_discrete_sequence=["#C8F135"],
                           labels={"LTV_Estimate": "Estimated LTV (GBP)"})
    fig_ltv.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#fff", height=240, margin=dict(t=10, b=40, l=60, r=20),
        showlegend=False, xaxis=dict(range=[0, p95] if p95 > 0 else None),
    )
    st.plotly_chart(fig_ltv, use_container_width=True, key="dash_ltv")
    st.caption(f"X-axis capped at the 95th percentile (£{p95:,.0f}) for readability. "
               f"{n_outliers} fans fall above this, up to £{max_ltv:,.0f}. Underlying values are unchanged.")

    # Row 4: Top fans tables
    t1, t2 = st.columns(2, gap="large")
    id_col = "Fan_ID" if "Fan_ID" in df.columns else df.columns[0]
    with t1:
        st.markdown('<div class="section-header">Top 10 Highest Value Fans</div>', unsafe_allow_html=True)
        top_val = df.nlargest(10, "LTV_Estimate")[[id_col, "LTV_Estimate", "Commercial_Score", "Segment"]]
        rows = [[
            f'<span style="color:#e5e7eb;font-weight:600;">{r[0]}</span>',
            f'<span style="color:#C8F135;font-weight:700;">&pound;{r[1]:,.0f}</span>',
            f'{r[2]:.0f}', str(r[3]),
        ] for r in top_val.itertuples(index=False)]
        st.markdown(html_table([id_col, "Est. LTV", "Commercial", "Segment"], rows), unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="section-header">Top 10 Highest Churn Risk</div>', unsafe_allow_html=True)
        top_churn = df.nlargest(10, "Churn_Risk")[[id_col, "Churn_Risk", "Commercial_Score", "Segment"]]
        rows = [[
            f'<span style="color:#e5e7eb;font-weight:600;">{r[0]}</span>',
            f'<span style="color:#f78186;font-weight:700;">{r[1]:.0f}</span>',
            f'{r[2]:.0f}', str(r[3]),
        ] for r in top_churn.itertuples(index=False)]
        st.markdown(html_table([id_col, "Churn Risk", "Commercial", "Segment"], rows), unsafe_allow_html=True)


# ── Tab 2: Campaign Intelligence ───────────────────────────────────────────
CAMPAIGN_CONFIG = {
    "VIP": {
        "objective": "Retain and deepen relationship with highest-value fans.",
        "angle": "Exclusive access and early recognition - make them feel seen.",
        "offer": "Priority season ticket renewal, VIP matchday experience, exclusive behind-the-scenes access.",
        "timing": "Send 6 weeks before season ticket renewal window opens.",
        "metric": "Renewal rate and upsell to premium hospitality.",
    },
    "High Potential": {
        "objective": "Convert engaged fans into members or season ticket holders.",
        "angle": "FOMO and value - show them what they are missing by not committing.",
        "offer": "Early bird season ticket offer with instalment payment option.",
        "timing": "Send immediately after a high-attendance fixture to capitalise on enthusiasm.",
        "metric": "Membership conversion rate and first ticket purchase.",
    },
    "Regular": {
        "objective": "Increase visit frequency and average transaction value.",
        "angle": "Community belonging - they already care, reward the habit.",
        "offer": "Bring a friend match ticket bundle, stadium dining offer.",
        "timing": "Send 10 days before next home fixture.",
        "metric": "Attendance uplift and secondary spend per visit.",
    },
    "Win Back": {
        "objective": "Re-engage fans who have drifted in the past 6 to 18 months.",
        "angle": "Nostalgia and we miss you - reference their last visit if data allows.",
        "offer": "Two-for-one match ticket to get them back through the door.",
        "timing": "Send mid-week, not on matchday. Give them time to plan.",
        "metric": "Click-through rate and first reattendance within 60 days.",
    },
    "Dormant": {
        "objective": "Low-cost reactivation or graceful suppression of unresponsive fans.",
        "angle": "Simple curiosity hook - what's new since you last visited.",
        "offer": "Free match ticket for one specific fixture as a reactivation gift.",
        "timing": "Send once. If no response within 30 days, move to suppression list.",
        "metric": "Open rate and link click. Anything above 5% is a win.",
    },
}

CHANNEL_MAP = {
    "Email": "Email",
    "SMS": "SMS",
    "Push Notification": "Push Notification",
    "Social": "Social Media",
    "Direct Mail": "Direct Mail",
}


def get_channel_for_segment(df: pd.DataFrame, segment: str) -> str:
    seg_df = df[df["Segment"] == segment]
    if "Channel_Preference" in df.columns and len(seg_df):
        top = seg_df["Channel_Preference"].value_counts().index[0]
        return CHANNEL_MAP.get(top, top)
    # Derive from age
    if "Age" in df.columns and len(seg_df):
        avg_age = seg_df["Age"].mean()
        if avg_age < 28:  return "Push Notification"
        elif avg_age < 42: return "Email"
        else:              return "Email + SMS"
    return "Email"


def get_conversion_est(df: pd.DataFrame, segment: str) -> float:
    seg_df = df[df["Segment"] == segment]
    if not len(seg_df):
        return 0.0
    base = {"VIP": 0.42, "High Potential": 0.28, "Regular": 0.18, "Win Back": 0.12, "Dormant": 0.05}
    base_rate = base.get(segment, 0.15)
    avg_eng = seg_df["Engagement_Score_Pct"].mean() / 100
    return round(base_rate * (0.7 + 0.6 * avg_eng), 3)


def render_campaign_intelligence(df: pd.DataFrame):
    st.markdown('<div class="section-header">Campaign Briefs - Auto-generated from your data</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#888;font-size:13px;">FanIQ generates a ready-to-execute brief for each fan segment based on their behaviour and commercial profile.</p>', unsafe_allow_html=True)

    seg_order = ["VIP", "High Potential", "Regular", "Win Back", "Dormant"]
    seg_counts = df["Segment"].value_counts()

    briefs_data = []
    for segment in seg_order:
        count = int(seg_counts.get(segment, 0))
        cfg = CAMPAIGN_CONFIG[segment]
        channel = get_channel_for_segment(df, segment)
        conv = get_conversion_est(df, segment)
        avg_val = segment_avg_value(df, segment)
        est_rev = count * avg_val * conv
        offer_ratio = OFFER_COST_RATIO.get(segment, 0.30)
        investment = est_rev * offer_ratio + count * channel_cost(channel)
        roi = est_rev / investment if investment > 0 else 0.0
        conf_label, conf_pct = confidence_score(df, count)
        faqi = segment_faqi_summary(df, segment)
        briefs_data.append({
            "segment": segment, "count": count, "channel": channel,
            "conv": conv, "est_revenue": est_rev, "roi": roi,
            "confidence": conf_label, "faqi": faqi,
            "est_revenue_str": f"GBP {est_rev:,.0f}", "roi_str": f"{roi:.1f}x",
            **cfg,
        })

    # Render brief cards — commercial tier (revenue/ROI/confidence) leads, brief detail is secondary
    def _brief_field(lbl, val, val_color="#c3c5cc"):
        return (f'<div><div style="font-size:10.5px;color:#7c7c86;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">{lbl}</div>'
                f'<div style="font-size:13px;color:{val_color};margin-top:5px;line-height:1.55;">{val}</div></div>')

    for b in briefs_data:
        color = SEGMENT_COLORS.get(b["segment"], "#888")
        pct = b["count"] / len(df) * 100 if len(df) else 0

        faqi_html = ""
        if b["faqi"]:
            fq = b["faqi"]
            fq_color = ATTENTION_COLORS[fq["status"]]
            faqi_html = (
                f'<div style="margin-top:16px;padding:11px 15px;background:#101018;border-radius:10px;'
                f'border-left:3px solid {fq_color};font-size:12.5px;color:#b7b9c0;">'
                f'Segment FAQI <span style="color:{fq_color};font-weight:700;">{fq["avg"]:.0f} ({fq["status"]})</span> '
                f'&middot; {ATTENTION_MEANING[fq["status"]]}</div>')

        secondary = (
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px 26px;margin-top:20px;'
            'padding-top:18px;border-top:1px solid #23232b;">'
            + _brief_field("Objective", b["objective"])
            + _brief_field("Channel", b["channel"], "#6ea8fe")
            + _brief_field("Message Angle", b["angle"])
            + _brief_field("Offer", b["offer"])
            + _brief_field("Timing", b["timing"])
            + _brief_field("Success Metric", b["metric"])
            + '</div>')

        st.markdown(f"""
        <div class="seg-card" style="border-top:3px solid {color};padding:24px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div class="seg-title" style="color:{color};">{b['segment']}</div>
                    <div class="seg-size">{b['count']:,} fans &middot; {pct:.1f}% of database</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:18px;font-weight:800;color:#e5e7eb;">{b['conv']*100:.0f}%</div>
                    <div style="font-size:10.5px;color:#7c7c86;text-transform:uppercase;letter-spacing:.05em;">Est. conversion</div>
                </div>
            </div>
            <div style="display:flex;gap:40px;align-items:flex-end;flex-wrap:wrap;margin-top:18px;">
                <div>
                    <div style="font-size:10.5px;color:#7c7c86;text-transform:uppercase;letter-spacing:.07em;font-weight:600;">Estimated Revenue</div>
                    <div style="font-size:28px;font-weight:800;color:#C8F135;margin-top:5px;line-height:1;">&pound;{b['est_revenue']:,.0f}</div>
                </div>
                <div>
                    <div style="font-size:10.5px;color:#7c7c86;text-transform:uppercase;letter-spacing:.07em;font-weight:600;">Estimated ROI</div>
                    <div style="font-size:28px;font-weight:800;color:#f3f4f6;margin-top:5px;line-height:1;">{b['roi']:.1f}x</div>
                </div>
                <div>
                    <div style="font-size:10.5px;color:#7c7c86;text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-bottom:9px;">Confidence</div>
                    {confidence_badge(b['confidence'])}
                </div>
            </div>
            {faqi_html}
            {secondary}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("What drives this score"):
            if b["faqi"]:
                st.markdown("**Top contributors**")
                for p in b["faqi"]["pos"]:
                    st.markdown(f"- ▲ {p}")
                for nneg in b["faqi"]["neg"]:
                    st.markdown(f"- ▼ {nneg}")
            else:
                st.caption("No fans currently in this segment.")

    # Download PDF
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬇ Download Campaign Briefs PDF"):
        pdf_bytes = generate_campaign_pdf(briefs_data)
        st.download_button("Download PDF", pdf_bytes, "faniq_campaign_briefs.pdf", "application/pdf")

    # Campaign Generator
    st.markdown('<div class="section-header">Campaign Generator</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#888;font-size:13px;">Select a segment and customise the brief before downloading.</p>', unsafe_allow_html=True)

    sel_seg = st.selectbox("Select segment", seg_order, key="camp_gen_seg")
    b = next(x for x in briefs_data if x["segment"] == sel_seg)

    # Streamlit retains widget state by key, so changing the `value` argument alone does NOT
    # refresh the fields when the segment changes. Explicitly reload the selected segment's
    # brief into session_state whenever the selection changes, so fields always match the segment.
    cg_defaults = {
        "cg_obj": b["objective"], "cg_angle": b["angle"], "cg_offer": b["offer"],
        "cg_channel": b["channel"], "cg_timing": b["timing"], "cg_metric": b["metric"],
    }
    if st.session_state.get("cg_last_seg") != sel_seg:
        for _k, _v in cg_defaults.items():
            st.session_state[_k] = _v
        st.session_state["cg_last_seg"] = sel_seg

    col_a, col_b = st.columns(2)
    with col_a:
        custom_obj = st.text_area("Objective", key="cg_obj")
        custom_angle = st.text_area("Message Angle", key="cg_angle")
        custom_offer = st.text_area("Offer", key="cg_offer")
    with col_b:
        custom_channel = st.text_input("Channel", key="cg_channel")
        custom_timing = st.text_area("Timing", key="cg_timing")
        custom_metric = st.text_area("Success Metric", key="cg_metric")

    if st.button("⬇ Download Custom Brief PDF"):
        custom_brief = [{
            "segment": sel_seg, "count": b["count"], "conv": b["conv"],
            "channel": custom_channel, "objective": custom_obj,
            "angle": custom_angle, "offer": custom_offer,
            "timing": custom_timing, "metric": custom_metric,
            "est_revenue_str": b["est_revenue_str"], "roi_str": b["roi_str"],
            "confidence": b["confidence"],
        }]
        pdf_bytes = generate_campaign_pdf(custom_brief)
        st.download_button("Download Custom PDF", pdf_bytes, f"faniq_{sel_seg.lower().replace(' ','_')}_brief.pdf", "application/pdf")


def generate_campaign_pdf(briefs: list) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 12, _pdf_safe("FanIQ - Campaign Briefs"), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, _pdf_safe(f"Generated {TODAY.strftime('%d %B %Y')}"), ln=True)
    pdf.ln(6)

    fields = [
        ("Objective", "objective"), ("Channel", "channel"), ("Message Angle", "angle"),
        ("Offer", "offer"), ("Timing", "timing"), ("Success Metric", "metric"),
        ("Estimated Revenue", "est_revenue_str"), ("Estimated ROI", "roi_str"),
        ("Confidence", "confidence"),
    ]

    for b in briefs:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(20, 20, 20)
        seg_label = _pdf_safe(f"{b['segment']} Segment - {b['count']:,} fans ({b['conv']*100:.0f}% est. conversion)")
        pdf.cell(0, 10, seg_label, ln=True)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        for label, key in fields:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 7, _pdf_safe(label), ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, _pdf_safe(b.get(key, "")))
            pdf.ln(2)
        pdf.ln(8)

    return bytes(pdf.output())


# ── Tab 3: Audience Story ──────────────────────────────────────────────────
def render_audience_story(df: pd.DataFrame):
    cols = set(df.columns)

    # Section 1: Who They Are
    who_lines = []
    if "Age" in cols:
        avg_age = df["Age"].mean()
        age_u35 = (df["Age"] < 35).sum() / len(df) * 100
        who_lines.append(f"The average fan is {avg_age:.0f} years old. {age_u35:.0f}% are under 35.")
    if "Gender" in cols:
        gc = df["Gender"].value_counts(normalize=True) * 100
        parts = [f"{pct:.0f}% {g}" for g, pct in gc.head(3).items()]
        who_lines.append(f"Gender breakdown: {', '.join(parts)}.")
    if "Country" in cols:
        top3 = df["Country"].value_counts().head(3)
        who_lines.append(f"Top markets: {', '.join(f'{c} ({n:,})' for c, n in top3.items())}.")
    if not who_lines:
        who_lines.append("Upload Age, Gender, and Country columns to unlock demographic intelligence.")
    avg_faqi = df["FAQI"].mean()
    faqi_status = attention_status(avg_faqi)
    who_lines.append(f"Average fan attention (FAQI) is {avg_faqi:.0f} ({faqi_status}) - commercially, {ATTENTION_MEANING[faqi_status]}")

    # Section 2: How They Behave
    beh_lines = []
    if "Tickets_Purchased" in cols:
        avg_tix = df["Tickets_Purchased"].mean()
        beh_lines.append(f"Fans purchase {avg_tix:.1f} tickets on average.")
    if "Spend" in cols:
        avg_spend = df["Spend"].mean()
        beh_lines.append(f"Average spend per fan is £{avg_spend:,.0f}.")
    if "Channel_Preference" in cols:
        top_ch = df["Channel_Preference"].value_counts().index[0]
        beh_lines.append(f"The most preferred communication channel is {top_ch}.")
    if "Membership_Type" in cols:
        top_mem = df["Membership_Type"].value_counts().index[0]
        none_pct = (df["Membership_Type"].str.lower() == "none").sum() / len(df) * 100
        beh_lines.append(f"Most common membership tier: {top_mem}. {none_pct:.0f}% have no membership.")
    if not beh_lines:
        beh_lines.append("Upload Tickets_Purchased, Spend, and Channel_Preference to unlock behavioural intelligence.")

    # Section 3: What They Are Worth
    worth_lines = []
    total_ltv = df["LTV_Estimate"].sum()
    avg_ltv = df["LTV_Estimate"].mean()
    worth_lines.append(f"Total estimated fanbase LTV: £{total_ltv:,.0f}. Average per fan: £{avg_ltv:,.0f}.")
    top20_ltv = df.nlargest(int(len(df) * 0.2), "LTV_Estimate")["LTV_Estimate"].sum()
    top20_pct = top20_ltv / total_ltv * 100 if total_ltv > 0 else 0
    worth_lines.append(f"The top 20% of fans account for {top20_pct:.0f}% of estimated lifetime value.")
    if "Spend" in cols:
        avg_spend = df["Spend"].mean()
        worth_lines.append(f"Average realised spend per fan: £{avg_spend:,.0f}.")

    # Section 4: Where The Opportunity Is
    opp_lines = []
    win_back_count = (df["Segment"] == "Win Back").sum()
    dormant_count = (df["Segment"] == "Dormant").sum()
    high_pot_count = (df["Segment"] == "High Potential").sum()
    opp_lines.append(f"{win_back_count:,} fans are in the Win Back segment - commercially active but drifting. These represent the highest immediate revenue recovery opportunity.")
    opp_lines.append(f"{dormant_count:,} fans are Dormant. A 10% reactivation rate would recover {dormant_count // 10:,} fans.")
    opp_lines.append(f"{high_pot_count:,} High Potential fans are engaged but not yet converted to membership - the clearest upsell pipeline.")
    if "Gender" in cols:
        f_pct = (df["Gender"].str.lower() == "female").sum() / len(df) * 100
        if f_pct < 35:
            opp_lines.append(f"Female fans make up {f_pct:.0f}% of the database. A dedicated female fan acquisition campaign is one option to broaden the commercial base.")

    # Section 5: What To Do Next
    vip_count = int((df["Segment"] == "VIP").sum())
    recs = [
        {
            "title": "Reactivate Win Back segment immediately",
            "rationale": f"{win_back_count:,} fans who have spent before are showing churn signals. A targeted two-for-one ticket offer sent via their preferred channel this week is the most direct route to recovering a meaningful share of this group.",
            "impact": f"Estimated revenue recovery: £{win_back_count * avg_ltv * 0.15:,.0f}",
            "confidence": confidence_score(df, win_back_count)[0],
            "effort": OPPORTUNITY_META["Win Back"]["effort"],
        },
        {
            "title": "Convert High Potential fans to membership",
            "rationale": f"{high_pot_count:,} fans score high on engagement but have not committed commercially. An early bird membership offer with instalment payment will close the gap.",
            "impact": f"Estimated new member revenue: £{high_pot_count * avg_ltv * 0.25:,.0f}",
            "confidence": confidence_score(df, high_pot_count)[0],
            "effort": OPPORTUNITY_META["High Potential"]["effort"],
        },
        {
            "title": "Protect VIP segment with a retention programme",
            "rationale": f"{seg_counts_for_story(df).get('VIP', 0):,} VIP fans represent a disproportionate share of revenue. Even a 5% churn in this group has outsized commercial impact.",
            "impact": "Preventing 5% VIP churn protects an estimated £{:,.0f} in LTV.".format(
                df[df["Segment"] == "VIP"]["LTV_Estimate"].sum() * 0.05
            ),
            "confidence": confidence_score(df, vip_count)[0],
            "effort": OPPORTUNITY_META["VIP"]["effort"],
        },
    ]

    # Render
    sections = [
        ("01. Who They Are", " ".join(who_lines)),
        ("02. How They Behave", " ".join(beh_lines)),
        ("03. What They Are Worth", " ".join(worth_lines)),
        ("04. Where The Opportunity Is", " ".join(opp_lines)),
    ]
    section_icons = ["◉", "↻", "◆", "◈"]
    for (title, body), icon in zip(sections, section_icons):
        st.markdown(f"""
        <div class="story-section">
            <div class="story-title"><span style="color:#C8F135;font-size:15px;">{icon}</span> {title}</div>
            <div class="story-body">{body}</div>
        </div>
        """, unsafe_allow_html=True)

    recs_html = ""
    for i, rec in enumerate(recs, 1):
        recs_html += (
            f'<div style="margin-bottom:26px;">'
            f'<div style="font-size:16px;font-weight:800;color:#f3f4f6;">{i}. {rec["title"]}</div>'
            f'<div style="font-size:14px;color:#c3c5cc;margin-top:9px;line-height:1.75;">{rec["rationale"]}</div>'
            f'<div style="font-size:14px;color:#C8F135;margin-top:11px;font-weight:700;">{rec["impact"]}</div>'
            f'<div style="margin-top:12px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
            f'<span style="font-size:11px;color:#7c7c86;text-transform:uppercase;letter-spacing:.05em;">Confidence</span>{confidence_badge(rec["confidence"])}'
            f'<span style="font-size:11px;color:#7c7c86;text-transform:uppercase;letter-spacing:.05em;margin-left:10px;">Effort</span>{effort_badge(rec["effort"])}'
            f'</div></div>')
    # Single markdown call so the recommendations render INSIDE the styled section box
    st.markdown(
        f'<div class="story-section" style="border-top:3px solid #C8F135;">'
        f'<div class="story-title"><span style="color:#C8F135;font-size:15px;">➜</span> 05. What To Do Next</div>'
        f'{recs_html}</div>',
        unsafe_allow_html=True)

    # Download PDF
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬇ Download Audience Story PDF"):
        pdf_bytes = generate_story_pdf(sections, recs)
        st.download_button("Download PDF", pdf_bytes, "faniq_audience_story.pdf", "application/pdf")


def seg_counts_for_story(df):
    return df["Segment"].value_counts().to_dict()


def generate_story_pdf(sections, recs) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 14, _pdf_safe("FanIQ - Audience Story"), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, _pdf_safe(f"Generated {TODAY.strftime('%d %B %Y')}"), ln=True)
    pdf.ln(8)

    for title, body in sections:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 10, _pdf_safe(title), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 6, _pdf_safe(body))
        pdf.ln(6)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, _pdf_safe("05. What To Do Next"), ln=True)
    for i, rec in enumerate(recs, 1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 8, _pdf_safe(f"{i}. {rec['title']}"), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 6, _pdf_safe(rec["rationale"]))
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(0, 100, 120)
        pdf.cell(0, 7, _pdf_safe(rec["impact"]), ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 6, _pdf_safe(f"Confidence: {rec.get('confidence', 'Medium')}  |  Effort: {rec.get('effort', 'Medium')}"), ln=True)
        pdf.ln(4)

    return bytes(pdf.output())


# ── Tab 4: Sponsorship Intelligence ───────────────────────────────────────
SPONSOR_CATEGORIES = [
    ("Sports Apparel", "HIGH", "Nike, Adidas, Puma", "Direct alignment with active fan lifestyle and club merchandise spend."),
    ("Financial Services", "HIGH", "Barclays, Revolut, Monzo", "Affluent core demographic with high commercial score makes financial products a natural fit."),
    ("Sports Nutrition", "MED", "Lucozade, Grenade, SIS", "Young male skew in engaged segments aligns with sports nutrition targeting."),
    ("Automotive", "MED", "Kia, Volkswagen, Ford", "Mid-tier commercial fans show car-ownership demographics and aspirational purchase intent."),
    ("Gaming & Esports", "MED", "EA Sports, Betway, DraftKings", "Under-35 fan cohort indexes high on digital gaming and sports betting platforms."),
    ("Travel", "LOW", "Booking.com, Airbnb, easyJet", "International fan base creates travel audience but purchase intent is harder to activate directly."),
]


def render_sponsorship_intelligence(df: pd.DataFrame):
    cols = set(df.columns)

    # Pitch score
    pitch_score = 58  # baseline
    pitch_score += (df["Commercial_Score"].mean() - 50) * 0.3
    if "Age" in cols:
        core_demo = ((df["Age"] >= 18) & (df["Age"] <= 35)).sum() / len(df) * 100
        pitch_score += (core_demo - 30) * 0.2
    if "Gender" in cols:
        female_pct = (df["Gender"].str.lower() == "female").sum() / len(df) * 100
        pitch_score += (female_pct - 25) * 0.15
    pitch_score = round(np.clip(pitch_score, 0, 100), 1)

    female_pct = ((df["Gender"].str.lower() == "female").sum() / len(df) * 100) if "Gender" in cols else 0
    core_demo_pct = (((df["Age"] >= 18) & (df["Age"] <= 35)).sum() / len(df) * 100) if "Age" in cols else 0
    top_market = df["Country"].value_counts().index[0] if "Country" in cols else "N/A"
    avg_comm = df["Commercial_Score"].mean()

    # KPI cards
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        gauge_color = "#C8F135" if pitch_score >= 65 else "#3B82F6" if pitch_score >= 50 else "#EF4444"
        st.markdown(kpi_card(f"{pitch_score:.0f}", "Sponsorship Pitch Index", "0-100 composite of your data", accent=gauge_color), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card(f"{female_pct:.0f}%", "Female Audience"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card(f"{core_demo_pct:.0f}%", "Core Demo 18-35"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card(f'<span style="font-size:24px;">{top_market}</span>', "Top Market"), unsafe_allow_html=True)

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # Charts row
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown('<div class="section-header">Gender Split</div>', unsafe_allow_html=True)
        if "Gender" in cols:
            gc = df["Gender"].value_counts()
            fig = go.Figure(go.Pie(
                labels=gc.index, values=gc.values, hole=0.5,
                marker_colors=["#3B82F6", "#C8F135", "#8B5CF6"],
                textinfo="label+percent", textfont_color="#fff",
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#fff", showlegend=False, height=300, margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True, key="spon_gender")
        else:
            st.info("Upload Gender column to unlock.")

    with ch2:
        st.markdown('<div class="section-header">Top Audience Markets</div>', unsafe_allow_html=True)
        if "Country" in cols:
            top_countries = df["Country"].value_counts().head(8)
            fig2 = px.bar(
                x=top_countries.values, y=top_countries.index, orientation="h",
                color_discrete_sequence=["#C8F135"],
                labels={"x": "Fans", "y": ""},
            )
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#fff", height=300, margin=dict(t=10,b=30,l=80,r=20),
                               yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig2, use_container_width=True, key="spon_countries")
        else:
            st.info("Upload Country column to unlock.")

    # Audience quality by segment
    st.markdown('<div class="section-header">Audience Quality by Segment</div>', unsafe_allow_html=True)
    seg_quality = df.groupby("Segment").agg(
        Fans=("Segment", "count"),
        Avg_Commercial=("Commercial_Score", "mean"),
        Avg_Engagement=("Engagement_Score_Pct", "mean"),
        Avg_LTV=("LTV_Estimate", "mean"),
    ).round(1).reset_index()
    rows = [[
        f'<span style="color:#e5e7eb;font-weight:600;">{r.Segment}</span>',
        f'{int(r.Fans):,}', f'{r.Avg_Commercial:.0f}', f'{r.Avg_Engagement:.0f}',
        f'<span style="color:#C8F135;font-weight:700;">&pound;{r.Avg_LTV:,.0f}</span>',
    ] for r in seg_quality.itertuples()]
    st.markdown(html_table(["Segment", "Fans", "Avg Commercial", "Avg Engagement", "Avg LTV"], rows), unsafe_allow_html=True)

    # Sponsor category recommendations
    st.markdown('<div class="section-header">Top Sponsor Category Recommendations</div>', unsafe_allow_html=True)
    rows = [[
        f'<span style="color:#e5e7eb;font-weight:600;">{cat}</span>',
        fit_badge(fit),
        f'<span style="color:#9ca3af;">{brands}</span>',
        f'<span style="color:#b7b9c0;">{why}</span>',
    ] for cat, fit, brands, why in SPONSOR_CATEGORIES]
    st.markdown(html_table(["Category", "Fit", "Example Brands", "Why It Fits"], rows), unsafe_allow_html=True)
    st.caption("Category fit is indicative guidance based on typical sports-fan demographics, "
               "not a per-fan calculation from your upload. Use the audience metrics above to validate.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬇ Download Sponsorship Deck PDF"):
        pdf_bytes = generate_sponsorship_pdf(pitch_score, female_pct, core_demo_pct, top_market, avg_comm, seg_quality)
        st.download_button("Download PDF", pdf_bytes, "faniq_sponsorship_deck.pdf", "application/pdf")


def generate_sponsorship_pdf(pitch_score, female_pct, core_demo_pct, top_market, avg_comm, seg_quality) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 14, _pdf_safe("FanIQ - Sponsorship Intelligence"), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, _pdf_safe(f"Generated {TODAY.strftime('%d %B %Y')}"), ln=True)
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, "Key Metrics", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for label, val in [
        ("Sponsorship Pitch Index", f"{pitch_score:.0f} / 100 (composite index)"),
        ("Female Audience", f"{female_pct:.0f}%"),
        ("Core Demo 18-35", f"{core_demo_pct:.0f}%"),
        ("Top Market", str(top_market)),
        ("Average Commercial Score", f"{avg_comm:.1f}"),
    ]:
        pdf.cell(60, 7, _pdf_safe(label + ":"), border=0)
        pdf.cell(0, 7, _pdf_safe(val), ln=True)
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Sponsor Category Recommendations", ln=True)
    for cat, fit, brands, why in SPONSOR_CATEGORIES:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 8, _pdf_safe(f"{cat} - Fit: {fit}"), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, _pdf_safe(f"Example brands: {brands}"), ln=True)
        pdf.multi_cell(0, 6, _pdf_safe(why))
        pdf.ln(4)

    return bytes(pdf.output())


# ── Tab 5: Player Influence ────────────────────────────────────────────────
def render_player_influence(df: pd.DataFrame):
    if not has_player_data(df):
        st.markdown("""
        <div class="story-section" style="text-align:center;padding:60px;">
            <div class="story-title" style="justify-content:center;">Player Influence Locked</div>
            <div class="story-body">Upload data with a <b>Favourite_Player</b> column to unlock Player Intelligence.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Exclude blank / Unknown player values so rankings reflect real players only
    _pl = df["Favourite_Player"].astype(str).str.strip()
    valid = df[~_pl.str.lower().isin(["", "unknown", "nan", "none"])]

    player_stats = valid.groupby("Favourite_Player").agg(
        Fan_Count=("Favourite_Player", "count"),
        Avg_Commercial=("Commercial_Score", "mean"),
        Avg_Engagement=("Engagement_Score_Pct", "mean"),
        Avg_LTV=("LTV_Estimate", "mean"),
        Avg_Conversion=("Conversion_Probability", "mean"),
    ).round(1).reset_index()

    # Composite marketing score
    player_stats["Marketing_Value"] = (
        player_stats["Avg_Engagement"] * 0.35 +
        player_stats["Avg_Commercial"] * 0.35 +
        player_stats["Avg_Conversion"] * 0.30
    ).round(1)

    club_avg_eng = df["Engagement_Score_Pct"].mean()
    player_stats["Sentiment_Lift"] = (player_stats["Avg_Engagement"] - club_avg_eng).round(1)
    club_avg_conv = df["Conversion_Probability"].mean()
    player_stats["Engagement_Multiplier"] = (player_stats["Avg_Engagement"] / max(club_avg_eng, 1)).round(2)
    player_stats["Merch_Index"] = _pct_rank(player_stats["Avg_Commercial"]).round(0).astype(int)

    player_stats = player_stats.sort_values("Marketing_Value", ascending=False).reset_index(drop=True)

    # Top player card
    top = player_stats.iloc[0]

    def _pmetric(label, val, color):
        return (f'<div><div style="font-size:10.5px;color:#8b8b95;text-transform:uppercase;letter-spacing:.07em;font-weight:600;">{label}</div>'
                f'<div style="font-size:24px;font-weight:800;color:{color};margin-top:6px;">{val}</div></div>')

    st.markdown(f"""
    <div class="seg-card" style="border-top:3px solid #C8F135;margin-bottom:24px;padding:26px;">
        <div class="seg-title">{top['Favourite_Player']}</div>
        <div class="seg-size">{int(top['Fan_Count']):,} fans &middot; Top Marketing Value Player</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-top:20px;">
            {_pmetric("Sentiment Lift", f"+{top['Sentiment_Lift']:.1f}", "#C8F135")}
            {_pmetric("Engagement Multiplier", f"{top['Engagement_Multiplier']:.2f}x", "#3B82F6")}
            {_pmetric("Merch Index", f"{int(top['Merch_Index'])}", "#8B5CF6")}
            {_pmetric("Marketing Value", f"{top['Marketing_Value']:.0f}", "#C8F135")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Bar chart - marketing value ranking
    st.markdown('<div class="section-header">Player Commercial Influence Ranking</div>', unsafe_allow_html=True)
    fig = px.bar(
        player_stats.head(15), x="Marketing_Value", y="Favourite_Player",
        orientation="h", color="Marketing_Value",
        color_continuous_scale=["#1a1a2e", "#C8F135"],
        labels={"Marketing_Value": "Marketing Value Score", "Favourite_Player": ""},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#fff", height=420, margin=dict(t=10, b=30, l=160, r=20),
        yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True, key="player_ranking")

    # Full table
    st.markdown('<div class="section-header">Full Player Sentiment Ranking</div>', unsafe_allow_html=True)
    rows = [[
        f'<span style="color:#e5e7eb;font-weight:600;">{r.Favourite_Player}</span>',
        f'{int(r.Fan_Count):,}',
        f'<span style="color:#C8F135;font-weight:700;">{r.Marketing_Value:.0f}</span>',
        f'{r.Sentiment_Lift:+.1f}',
        f'{r.Engagement_Multiplier:.2f}x',
        f'{int(r.Merch_Index)}',
        f'&pound;{r.Avg_LTV:,.0f}',
    ] for r in player_stats.head(20).itertuples()]
    st.markdown(html_table(
        ["Player", "Fans", "Marketing Value", "Sentiment Lift", "Eng. Multiplier", "Merch Index", "Avg LTV"],
        rows), unsafe_allow_html=True)


# ── Main App ───────────────────────────────────────────────────────────────
def main():
    # Init session state
    if "df_raw" not in st.session_state:
        st.session_state["df_raw"] = None
    if "df" not in st.session_state:
        st.session_state["df"] = None

    # Upload screen
    if st.session_state["df_raw"] is None:
        render_upload_screen()
        return

    # Process data once — with a brief native analysis screen
    if st.session_state["df"] is None:
        raw = st.session_state["df_raw"]
        with st.status("Analysing your fanbase...", expanded=True) as status:
            st.write("Mapping uploaded fan data...")
            mapping = fuzzy_map_columns(raw)
            df = remap_df(raw, mapping)
            matched_core = [c for c in ["Fan_ID","Age","Gender","Last_Attended","Tickets_Purchased",
                                         "Spend","Membership_Type","Engagement_Score"] if c in df.columns]
            time.sleep(0.5)
            st.write("Calculating FAQI scores...")
            df = compute_scores(df)
            time.sleep(0.5)
            st.write("Identifying commercial opportunities...")
            time.sleep(0.5)
            st.write("Preparing Commercial Outlook...")
            time.sleep(0.5)
            status.update(label="Analysis complete", state="complete", expanded=False)
        st.session_state["df"] = df
        st.session_state["mapping"] = mapping
        st.session_state["matched_core"] = matched_core

    df = st.session_state["df"]
    mapping = st.session_state.get("mapping", {})
    matched_core = st.session_state.get("matched_core", [])

    # Platform header
    st.markdown("""
    <div class="platform-header">
        <div class="platform-name">⚡ FanIQ</div>
        <div class="platform-tag">FanIQ helps sports organisations identify, prioritise and act on their highest-value commercial opportunities using fan intelligence.</div>
    </div>
    """, unsafe_allow_html=True)

    # Header row: mapped columns info + Executive Brief + reset
    h1, h2, h3 = st.columns([4, 1, 1])
    with h1:
        mapped_str = " · ".join(f"<span style='color:#8fae5a'>{k}</span>" for k in mapping.keys())
        st.markdown(f'<p style="font-size:12px;color:#7c7c86;margin-top:4px;">{len(df):,} fans · Mapped: {mapped_str}</p>', unsafe_allow_html=True)
    with h2:
        if st.button("Executive Brief"):
            st.session_state["exec_brief_pdf"] = generate_executive_brief_pdf(df)
    with h3:
        if st.button("↩ New Upload"):
            st.session_state["df_raw"] = None
            st.session_state["df"] = None
            st.session_state.pop("exec_brief_pdf", None)
            st.rerun()

    if st.session_state.get("exec_brief_pdf"):
        st.download_button(
            "⬇ Download Executive Brief PDF", st.session_state["exec_brief_pdf"],
            "faniq_executive_brief.pdf", "application/pdf", key="exec_brief_dl")

    # Show tabs - hybrid schema: fewer than 5 core = only Custom Metrics
    if len(matched_core) < 5:
        st.warning(f"Only {len(matched_core)} core columns matched. Showing Custom Metrics Explorer only.")
        st.markdown('<div class="section-header">Custom Metrics Explorer</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        return

    has_player = has_player_data(df)

    if has_player:
        tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Commercial Outlook", "Fan Dashboard", "Campaign Intelligence",
            "Audience Story", "Sponsorship Intelligence", "Player Influence",
        ])
    else:
        tab0, tab1, tab2, tab3, tab4 = st.tabs([
            "Commercial Outlook", "Fan Dashboard", "Campaign Intelligence",
            "Audience Story", "Sponsorship Intelligence",
        ])

    with tab0:
        render_commercial_outlook(df)

    with tab1:
        render_fan_dashboard(df)

    with tab2:
        render_campaign_intelligence(df)

    with tab3:
        render_audience_story(df)

    with tab4:
        render_sponsorship_intelligence(df)

    if has_player:
        with tab5:
            render_player_influence(df)


if __name__ == "__main__":
    main()
