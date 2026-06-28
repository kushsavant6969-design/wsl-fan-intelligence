"""
FanIQ — Know your fans. Act on the insight.
Sport-agnostic fan segmentation and campaign intelligence platform.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io, random, os
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

[data-testid="stAppViewContainer"] { background: #080810 !important; }
[data-testid="stHeader"]           { background: #080810 !important; border-bottom: 1px solid #1a1a2e; }
section[data-testid="stSidebar"]   { display: none; }
.block-container { padding: 0 2rem 2rem !important; max-width: 100% !important; }

/* Tabs */
[data-testid="stTabs"] > div:first-child { border-bottom: 2px solid #1a1a2e; }
button[data-baseweb="tab"] {
    color: #666 !important; font-size: 13px !important; font-weight: 500 !important;
    padding: 10px 20px !important; border-radius: 6px 6px 0 0 !important;
    border: none !important; background: transparent !important;
}
button[data-baseweb="tab"]:hover { color: #E8FF00 !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #E8FF00 !important; border-bottom: 2px solid #E8FF00 !important;
    background: #0d0d1a !important; font-weight: 700 !important;
}
[data-testid="stTabsContent"] { padding-top: 1.5rem !important; }

/* Inputs */
[data-testid="stTextInput"] input { background: #0d0d1a !important; color: #fff !important; border: 1px solid #2a2a4a !important; }
[data-testid="stSelectbox"] > div > div { background: #0d0d1a !important; color: #fff !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: #0d0d1a !important; border: 2px dashed #E8FF00 !important;
    border-radius: 12px !important; padding: 2rem !important;
}
[data-testid="stFileUploader"] label { color: #fff !important; }

/* Buttons */
.stButton > button {
    background: #E8FF00 !important; color: #080810 !important;
    font-weight: 700 !important; border: none !important;
    border-radius: 8px !important; padding: 10px 24px !important;
}
.stButton > button:hover { background: #00E5FF !important; }
.stDownloadButton > button {
    background: #1a1a2e !important; color: #E8FF00 !important;
    border: 1px solid #E8FF00 !important; font-weight: 600 !important;
    border-radius: 8px !important;
}

/* KPI cards */
.kpi-card {
    background: #0d0d1a; border: 1px solid #2a2a4a; border-radius: 12px;
    padding: 20px; text-align: center;
}
.kpi-value { font-size: 32px; font-weight: 800; color: #E8FF00; }
.kpi-label { font-size: 12px; color: #888; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }
.kpi-sub   { font-size: 13px; color: #00E5FF; margin-top: 6px; }

/* Segment cards */
.seg-card {
    background: #0d0d1a; border: 1px solid #2a2a4a; border-radius: 12px;
    padding: 20px; margin-bottom: 16px;
}
.seg-title { font-size: 18px; font-weight: 700; color: #E8FF00; }
.seg-size  { font-size: 13px; color: #888; }

/* Section headers */
.section-header {
    font-size: 20px; font-weight: 700; color: #fff;
    border-left: 4px solid #E8FF00; padding-left: 12px;
    margin: 28px 0 16px 0;
}

/* Story sections */
.story-section {
    background: #0d0d1a; border-radius: 12px; padding: 28px;
    margin-bottom: 20px; border-left: 4px solid #E8FF00;
}
.story-title { font-size: 22px; font-weight: 800; color: #E8FF00; margin-bottom: 12px; }
.story-body  { font-size: 15px; color: #ccc; line-height: 1.8; }

/* Tables */
[data-testid="stDataFrame"] { border-radius: 8px !important; }

/* Platform header */
.platform-header {
    padding: 24px 0 12px 0;
    border-bottom: 1px solid #1a1a2e;
    margin-bottom: 24px;
}
.platform-name { font-size: 28px; font-weight: 800; color: #E8FF00; letter-spacing: -1px; }
.platform-tag  { font-size: 14px; color: #888; margin-top: 4px; }

/* Upload info grid */
.col-info {
    background: #0d0d1a; border: 1px solid #2a2a4a; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 8px;
}
.col-name   { font-size: 13px; font-weight: 700; color: #00E5FF; }
.col-unlock { font-size: 12px; color: #888; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

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
    "VIP":            "#E8FF00",
    "High Potential": "#00E5FF",
    "Regular":        "#7B68EE",
    "Win Back":       "#FF6B6B",
    "Dormant":        "#555",
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

    return df


# ── Upload Screen ──────────────────────────────────────────────────────────
def render_upload_screen():
    st.markdown("""
    <div class="platform-header">
        <div class="platform-name">⚡ FanIQ</div>
        <div class="platform-tag">Know your fans. Act on the insight.</div>
    </div>
    """, unsafe_allow_html=True)

    col_up, col_info = st.columns([3, 2], gap="large")

    with col_up:
        st.markdown('<div class="section-header">Upload Your Fan Database</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#888;font-size:13px;">Any CSV format. FanIQ auto-detects columns — no template required.</p>', unsafe_allow_html=True)

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
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{len(df):,}</div><div class="kpi-label">Total Fans</div></div>', unsafe_allow_html=True)
    with k2:
        avg_comm = df["Commercial_Score"].mean()
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{avg_comm:.0f}</div><div class="kpi-label">Avg Commercial Score</div><div class="kpi-sub">0–100 percentile</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{high_churn:,}</div><div class="kpi-label">High Churn Risk</div><div class="kpi-sub">Score ≥ 70</div></div>', unsafe_allow_html=True)
    with k4:
        top_count = seg_counts.iloc[0] if len(seg_counts) else 0
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{top_count:,}</div><div class="kpi-label">Top Segment</div><div class="kpi-sub">{top_seg}</div></div>', unsafe_allow_html=True)

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
        stage_counts = df["Journey_Stage"].value_counts().sort_index()
        stages = [stage_labels[i] for i in range(1, 6)]
        counts = [stage_counts.get(i, 0) for i in range(1, 6)]
        fig2 = go.Figure(go.Funnel(
            y=stages, x=counts,
            textinfo="value+percent initial",
            marker_color=["#E8FF00", "#b8cc00", "#00E5FF", "#00b8cc", "#7B68EE"],
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#fff", margin=dict(t=20, b=20, l=120, r=20), height=320,
        )
        st.plotly_chart(fig2, use_container_width=True, key="dash_funnel")

    # Row 2: Score distributions
    st.markdown('<div class="section-header">Score Distributions</div>', unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    score_cols = [
        ("Engagement_Score_Pct", "Engagement", "#E8FF00", s1, "dash_eng"),
        ("Commercial_Score", "Commercial", "#00E5FF", s2, "dash_comm"),
        ("Loyalty_Score", "Loyalty", "#7B68EE", s3, "dash_loy"),
        ("Churn_Risk", "Churn Risk", "#FF6B6B", s4, "dash_churn"),
        ("Conversion_Probability", "Conversion", "#00FF88", s5, "dash_conv"),
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
    fig_ltv = px.histogram(df, x="LTV_Estimate", nbins=30,
                           color_discrete_sequence=["#E8FF00"],
                           labels={"LTV_Estimate": "Estimated LTV"})
    fig_ltv.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#fff", height=240, margin=dict(t=10, b=40, l=60, r=20),
        showlegend=False,
    )
    st.plotly_chart(fig_ltv, use_container_width=True, key="dash_ltv")

    # Row 4: Top fans tables
    t1, t2 = st.columns(2)
    with t1:
        st.markdown('<div class="section-header">Top 10 Highest Value Fans</div>', unsafe_allow_html=True)
        id_col = "Fan_ID" if "Fan_ID" in df.columns else df.columns[0]
        top_val = df.nlargest(10, "LTV_Estimate")[[id_col, "LTV_Estimate", "Commercial_Score", "Segment"]].reset_index(drop=True)
        st.dataframe(top_val, use_container_width=True, hide_index=True)

    with t2:
        st.markdown('<div class="section-header">Top 10 Highest Churn Risk</div>', unsafe_allow_html=True)
        top_churn = df.nlargest(10, "Churn_Risk")[[id_col, "Churn_Risk", "Commercial_Score", "Segment"]].reset_index(drop=True)
        st.dataframe(top_churn, use_container_width=True, hide_index=True)


# ── Tab 2: Campaign Intelligence ───────────────────────────────────────────
CAMPAIGN_CONFIG = {
    "VIP": {
        "objective": "Retain and deepen relationship with highest-value fans.",
        "angle": "Exclusive access and early recognition — make them feel seen.",
        "offer": "Priority season ticket renewal, VIP matchday experience, exclusive behind-the-scenes access.",
        "timing": "Send 6 weeks before season ticket renewal window opens.",
        "metric": "Renewal rate and upsell to premium hospitality.",
    },
    "High Potential": {
        "objective": "Convert engaged fans into members or season ticket holders.",
        "angle": "FOMO and value — show them what they are missing by not committing.",
        "offer": "Early bird season ticket offer with instalment payment option.",
        "timing": "Send immediately after a high-attendance fixture to capitalise on enthusiasm.",
        "metric": "Membership conversion rate and first ticket purchase.",
    },
    "Regular": {
        "objective": "Increase visit frequency and average transaction value.",
        "angle": "Community belonging — they already care, reward the habit.",
        "offer": "Bring a friend match ticket bundle, stadium dining offer.",
        "timing": "Send 10 days before next home fixture.",
        "metric": "Attendance uplift and secondary spend per visit.",
    },
    "Win Back": {
        "objective": "Re-engage fans who have drifted in the past 6 to 18 months.",
        "angle": "Nostalgia and we miss you — reference their last visit if data allows.",
        "offer": "Two-for-one match ticket to get them back through the door.",
        "timing": "Send mid-week, not on matchday. Give them time to plan.",
        "metric": "Click-through rate and first reattendance within 60 days.",
    },
    "Dormant": {
        "objective": "Low-cost reactivation or graceful suppression of unresponsive fans.",
        "angle": "Simple curiosity hook — what's new since you last visited.",
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
    st.markdown('<div class="section-header">Campaign Briefs — Auto-generated from your data</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#888;font-size:13px;">FanIQ generates a ready-to-execute brief for each fan segment based on their behaviour and commercial profile.</p>', unsafe_allow_html=True)

    seg_order = ["VIP", "High Potential", "Regular", "Win Back", "Dormant"]
    seg_counts = df["Segment"].value_counts()

    briefs_data = []
    for segment in seg_order:
        count = seg_counts.get(segment, 0)
        cfg = CAMPAIGN_CONFIG[segment]
        channel = get_channel_for_segment(df, segment)
        conv = get_conversion_est(df, segment)
        briefs_data.append({
            "segment": segment, "count": count, "channel": channel,
            "conv": conv, **cfg,
        })

    # Render brief cards
    for b in briefs_data:
        color = SEGMENT_COLORS.get(b["segment"], "#888")
        pct = b["count"] / len(df) * 100 if len(df) else 0
        conv_pct = b["conv"] * 100

        st.markdown(f"""
        <div class="seg-card" style="border-left: 4px solid {color};">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div class="seg-title" style="color:{color};">{b['segment']}</div>
                    <div class="seg-size">{b['count']:,} fans · {pct:.1f}% of database</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:22px;font-weight:800;color:{color};">{conv_pct:.0f}%</div>
                    <div style="font-size:11px;color:#888;">Est. conversion</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;">
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Objective</div>
                    <div style="font-size:13px;color:#ddd;margin-top:4px;">{b['objective']}</div>
                </div>
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Channel</div>
                    <div style="font-size:13px;color:#00E5FF;margin-top:4px;">{b['channel']}</div>
                </div>
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Message Angle</div>
                    <div style="font-size:13px;color:#ddd;margin-top:4px;">{b['angle']}</div>
                </div>
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Offer</div>
                    <div style="font-size:13px;color:#ddd;margin-top:4px;">{b['offer']}</div>
                </div>
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Timing</div>
                    <div style="font-size:13px;color:#ddd;margin-top:4px;">{b['timing']}</div>
                </div>
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Success Metric</div>
                    <div style="font-size:13px;color:#ddd;margin-top:4px;">{b['metric']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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

    col_a, col_b = st.columns(2)
    with col_a:
        custom_obj = st.text_area("Objective", b["objective"], key="cg_obj")
        custom_angle = st.text_area("Message Angle", b["angle"], key="cg_angle")
        custom_offer = st.text_area("Offer", b["offer"], key="cg_offer")
    with col_b:
        custom_channel = st.text_input("Channel", b["channel"], key="cg_channel")
        custom_timing = st.text_area("Timing", b["timing"], key="cg_timing")
        custom_metric = st.text_area("Success Metric", b["metric"], key="cg_metric")

    if st.button("⬇ Download Custom Brief PDF"):
        custom_brief = [{
            "segment": sel_seg, "count": b["count"], "conv": b["conv"],
            "channel": custom_channel, "objective": custom_obj,
            "angle": custom_angle, "offer": custom_offer,
            "timing": custom_timing, "metric": custom_metric,
        }]
        pdf_bytes = generate_campaign_pdf(custom_brief)
        st.download_button("Download Custom PDF", pdf_bytes, f"faniq_{sel_seg.lower().replace(' ','_')}_brief.pdf", "application/pdf")


def generate_campaign_pdf(briefs: list) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 12, _pdf_safe("FanIQ — Campaign Briefs"), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, _pdf_safe(f"Generated {TODAY.strftime('%d %B %Y')}"), ln=True)
    pdf.ln(6)

    fields = [
        ("Objective", "objective"), ("Channel", "channel"), ("Message Angle", "angle"),
        ("Offer", "offer"), ("Timing", "timing"), ("Success Metric", "metric"),
    ]

    for b in briefs:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(20, 20, 20)
        seg_label = _pdf_safe(f"{b['segment']} Segment — {b['count']:,} fans ({b['conv']*100:.0f}% est. conversion)")
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

    # Section 2: How They Behave
    beh_lines = []
    if "Tickets_Purchased" in cols:
        avg_tix = df["Tickets_Purchased"].mean()
        beh_lines.append(f"Fans purchase {avg_tix:.1f} tickets on average per season.")
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
    opp_lines.append(f"{win_back_count:,} fans are in the Win Back segment — commercially active but drifting. These represent the highest immediate revenue recovery opportunity.")
    opp_lines.append(f"{dormant_count:,} fans are Dormant. A 10% reactivation rate would recover {dormant_count // 10:,} fans.")
    opp_lines.append(f"{high_pot_count:,} High Potential fans are engaged but not yet converted to membership — the clearest upsell pipeline.")
    if "Gender" in cols:
        f_pct = (df["Gender"].str.lower() == "female").sum() / len(df) * 100
        if f_pct < 35:
            opp_lines.append(f"Female representation at {f_pct:.0f}% is below industry benchmark of 40%. A targeted female fan acquisition campaign is recommended.")

    # Section 5: What To Do Next
    recs = [
        {
            "title": "Reactivate Win Back segment immediately",
            "rationale": f"{win_back_count:,} fans who have spent before are showing churn signals. A targeted two-for-one ticket offer sent via their preferred channel this week is projected to recover 12-18% of this group.",
            "impact": f"Estimated revenue recovery: £{win_back_count * avg_ltv * 0.15:,.0f}",
        },
        {
            "title": "Convert High Potential fans to membership",
            "rationale": f"{high_pot_count:,} fans score high on engagement but have not committed commercially. An early bird membership offer with instalment payment will close the gap.",
            "impact": f"Estimated new member revenue: £{high_pot_count * avg_ltv * 0.25:,.0f}",
        },
        {
            "title": "Protect VIP segment with a retention programme",
            "rationale": f"{seg_counts_for_story(df).get('VIP', 0):,} VIP fans represent a disproportionate share of revenue. Even a 5% churn in this group has outsized commercial impact.",
            "impact": "Preventing 5% VIP churn protects an estimated £{:,.0f} in LTV.".format(
                df[df["Segment"] == "VIP"]["LTV_Estimate"].sum() * 0.05
            ),
        },
    ]

    # Render
    sections = [
        ("01. Who They Are", " ".join(who_lines)),
        ("02. How They Behave", " ".join(beh_lines)),
        ("03. What They Are Worth", " ".join(worth_lines)),
        ("04. Where The Opportunity Is", " ".join(opp_lines)),
    ]
    for title, body in sections:
        st.markdown(f"""
        <div class="story-section">
            <div class="story-title">{title}</div>
            <div class="story-body">{body}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="story-section" style="border-left:4px solid #00E5FF;">
        <div class="story-title" style="color:#00E5FF;">05. What To Do Next</div>
    """, unsafe_allow_html=True)
    for i, rec in enumerate(recs, 1):
        st.markdown(f"""
        <div style="margin-bottom:20px;">
            <div style="font-size:16px;font-weight:700;color:#fff;">{i}. {rec['title']}</div>
            <div style="font-size:14px;color:#ccc;margin-top:6px;line-height:1.7;">{rec['rationale']}</div>
            <div style="font-size:13px;color:#00E5FF;margin-top:6px;font-weight:600;">{rec['impact']}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

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
    pdf.cell(0, 14, _pdf_safe("FanIQ — Audience Story"), ln=True)
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
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        gauge_color = "#E8FF00" if pitch_score >= 65 else "#00E5FF" if pitch_score >= 50 else "#FF6B6B"
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:{gauge_color};">{pitch_score:.0f}</div><div class="kpi-label">Sponsorship Pitch Score</div><div class="kpi-sub">Benchmark: 58</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{female_pct:.0f}%</div><div class="kpi-label">Female Audience</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{core_demo_pct:.0f}%</div><div class="kpi-label">Core Demo 18-35</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{top_market}</div><div class="kpi-label">Top Market</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown('<div class="section-header">Gender Split</div>', unsafe_allow_html=True)
        if "Gender" in cols:
            gc = df["Gender"].value_counts()
            fig = go.Figure(go.Pie(
                labels=gc.index, values=gc.values, hole=0.5,
                marker_colors=["#00E5FF", "#E8FF00", "#7B68EE"],
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
                color_discrete_sequence=["#E8FF00"],
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
    st.dataframe(seg_quality, use_container_width=True, hide_index=True)

    # Sponsor category recommendations
    st.markdown('<div class="section-header">Top Sponsor Category Recommendations</div>', unsafe_allow_html=True)
    spon_df = pd.DataFrame(SPONSOR_CATEGORIES, columns=["Category", "Fit", "Example Brands", "Why It Fits"])
    st.dataframe(spon_df, use_container_width=True, hide_index=True)

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
    pdf.cell(0, 14, _pdf_safe("FanIQ — Sponsorship Intelligence"), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, _pdf_safe(f"Generated {TODAY.strftime('%d %B %Y')}"), ln=True)
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, "Key Metrics", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for label, val in [
        ("Sponsorship Pitch Score", f"{pitch_score:.0f} / 100 (benchmark: 58)"),
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
        pdf.cell(0, 8, _pdf_safe(f"{cat} — Fit: {fit}"), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, _pdf_safe(f"Example brands: {brands}"), ln=True)
        pdf.multi_cell(0, 6, _pdf_safe(why))
        pdf.ln(4)

    return bytes(pdf.output())


# ── Tab 5: Player Influence ────────────────────────────────────────────────
def render_player_influence(df: pd.DataFrame):
    if "Favourite_Player" not in df.columns:
        st.markdown("""
        <div class="story-section" style="text-align:center;padding:60px;">
            <div class="story-title">Player Influence Locked</div>
            <div class="story-body">Upload data with a <b>Favourite_Player</b> column to unlock Player Intelligence.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    player_stats = df.groupby("Favourite_Player").agg(
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
    st.markdown(f"""
    <div class="seg-card" style="border-left:4px solid #E8FF00;margin-bottom:24px;">
        <div class="seg-title">⭐ {top['Favourite_Player']}</div>
        <div class="seg-size">{int(top['Fan_Count']):,} fans · Top Marketing Value Player</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:16px;">
            <div>
                <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Sentiment Lift</div>
                <div style="font-size:24px;font-weight:800;color:#E8FF00;">+{top['Sentiment_Lift']:.1f}</div>
            </div>
            <div>
                <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Engagement Multiplier</div>
                <div style="font-size:24px;font-weight:800;color:#00E5FF;">{top['Engagement_Multiplier']:.2f}x</div>
            </div>
            <div>
                <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Merch Index</div>
                <div style="font-size:24px;font-weight:800;color:#7B68EE;">{int(top['Merch_Index'])}</div>
            </div>
            <div>
                <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Marketing Value</div>
                <div style="font-size:24px;font-weight:800;color:#00FF88;">{top['Marketing_Value']:.0f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Bar chart — marketing value ranking
    st.markdown('<div class="section-header">Player Commercial Influence Ranking</div>', unsafe_allow_html=True)
    fig = px.bar(
        player_stats.head(15), x="Marketing_Value", y="Favourite_Player",
        orientation="h", color="Marketing_Value",
        color_continuous_scale=["#1a1a2e", "#E8FF00"],
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
    display_cols = ["Favourite_Player", "Fan_Count", "Marketing_Value", "Sentiment_Lift",
                    "Engagement_Multiplier", "Merch_Index", "Avg_LTV"]
    st.dataframe(player_stats[display_cols], use_container_width=True, hide_index=True)


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

    # Process data once
    if st.session_state["df"] is None:
        raw = st.session_state["df_raw"]
        mapping = fuzzy_map_columns(raw)
        df = remap_df(raw, mapping)
        matched_core = [c for c in ["Fan_ID","Age","Gender","Last_Attended","Tickets_Purchased",
                                     "Spend","Membership_Type","Engagement_Score"] if c in df.columns]
        df = compute_scores(df)
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
        <div class="platform-tag">Know your fans. Act on the insight.</div>
    </div>
    """, unsafe_allow_html=True)

    # Header row: mapped columns info + reset
    h1, h2 = st.columns([5, 1])
    with h1:
        mapped_str = " · ".join(f"<span style='color:#00E5FF'>{k}</span>" for k in mapping.keys())
        st.markdown(f'<p style="font-size:12px;color:#666;">{len(df):,} fans · Mapped: {mapped_str}</p>', unsafe_allow_html=True)
    with h2:
        if st.button("↩ New Upload"):
            st.session_state["df_raw"] = None
            st.session_state["df"] = None
            st.rerun()

    # Show tabs — hybrid schema: fewer than 5 core = only Custom Metrics
    if len(matched_core) < 5:
        st.warning(f"Only {len(matched_core)} core columns matched. Showing Custom Metrics Explorer only.")
        st.markdown('<div class="section-header">Custom Metrics Explorer</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        return

    has_player = "Favourite_Player" in df.columns

    if has_player:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Fan Dashboard", "Campaign Intelligence", "Audience Story",
            "Sponsorship Intelligence", "Player Influence",
        ])
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "Fan Dashboard", "Campaign Intelligence", "Audience Story",
            "Sponsorship Intelligence",
        ])

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
