"""
FootIntel – Fan Intelligence Platform
Standalone Streamlit app: upload fan CSV → analyse → act.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import io
from datetime import datetime, timedelta

try:
    from rapidfuzz import fuzz as rfuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FootIntel | Fan Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS (dark theme matching WSL app palette) ────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Mono',monospace;}
[data-testid="stAppViewContainer"]{background:#0a0c10;}
[data-testid="stHeader"]{background:#0a0c10;}
section[data-testid="stSidebar"]{display:none;}
div[data-testid="stRadio"]>label{display:none;}
div[data-testid="stRadio"]>div{flex-direction:row;flex-wrap:wrap;gap:8px;}
div[data-testid="stRadio"]>div>label{
    background:#13161d!important;border:1px solid #2a2f3d!important;
    border-radius:6px!important;padding:7px 18px!important;
    color:#9ca3af!important;font-family:'DM Mono',monospace!important;
    font-size:12px!important;cursor:pointer!important;transition:.15s!important;}
div[data-testid="stRadio"]>div>label:has(input:checked){
    background:#c8f135!important;border-color:#c8f135!important;
    color:#0a0c10!important;font-weight:500!important;}
div[data-testid="stRadio"]>div>label>div>div:has(input[type="radio"]){display:none!important;}
.block-container{padding:2rem 2rem 1rem!important;}
h1,h2,h3{font-family:'Syne',sans-serif!important;}
.stSpinner>div{border-top-color:#c8f135!important;}
div[data-testid="stButton"]>button{
    background:#13161d!important;border:1px solid #2a2f3d!important;
    color:#9ca3af!important;font-family:'DM Mono',monospace!important;
    font-size:10px!important;padding:5px 16px!important;border-radius:6px!important;}
div[data-testid="stButton"]>button:hover{border-color:#c8f135!important;color:#c8f135!important;}
textarea{background:#13161d!important;color:#e5e7eb!important;
         border:1px solid #2a2f3d!important;font-family:'DM Mono',monospace!important;}
.stSelectbox>div>div{background:#13161d!important;border:1px solid #2a2f3d!important;color:#e5e7eb!important;}
@media(max-width:768px){
    .block-container{padding:1rem!important;}
    [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;}
    [data-testid="column"]{min-width:100%!important;flex:1 1 100%!important;}
    div[data-testid="stRadio"]>div>label{
        flex:1 1 calc(50% - 8px)!important;text-align:center!important;padding:8px 10px!important;}
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _pdf_safe(t: str) -> str:
    """Sanitise text for FPDF latin-1 output."""
    return (
        str(t)
        .replace("—", " - ")
        .replace("–", "-")
        .replace("•", "-")
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace(" ", " ")
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


def insight_banner(sentence1: str, sentence2: str) -> None:
    """Gold left-border dark card, 2-sentence insight."""
    st.markdown(
        f'<div style="background:#13161d;border-left:4px solid #c8a800;'
        f'border-radius:8px;padding:14px 20px;margin-bottom:22px">'
        f'<span style="color:#c8a800;font-size:10px;text-transform:uppercase;'
        f'letter-spacing:.12em;font-weight:600">AI Insight</span><br>'
        f'<span style="color:#f3f4f6;font-size:13px;line-height:1.7">'
        f'{sentence1} {sentence2}</span></div>',
        unsafe_allow_html=True,
    )


def card(content, padding="16px 18px", bg="#13161d", border="#2a2f3d", radius="10px"):
    return (
        f'<div style="background:{bg};border:1px solid {border};'
        f'border-radius:{radius};padding:{padding};margin-bottom:14px">{content}</div>'
    )


def kpi(label, value, sub="", color="#c8f135"):
    return f"""
    <div style="background:#13161d;border:1px solid #1f2937;border-radius:10px;
                padding:18px 20px;height:100%">
      <div style="font-size:10px;color:#6b7280;text-transform:uppercase;
                  letter-spacing:.1em;margin-bottom:8px">{label}</div>
      <div style="font-family:'Syne',sans-serif;font-size:32px;font-weight:800;
                  color:{color};line-height:1">{value}</div>
      <div style="font-size:11px;color:#9ca3af;margin-top:6px">{sub}</div>
    </div>"""


def section_header(title: str, subtitle: str = "") -> None:
    sub_html = (
        f'<p style="color:#6b7280;font-size:12px;margin:2px 0 12px">{subtitle}</p>'
        if subtitle else '<div style="margin-bottom:12px"></div>'
    )
    st.markdown(
        f'<h3 style="font-family:\'Syne\',sans-serif;color:#e5e7eb;'
        f'font-size:17px;margin-bottom:2px">{title}</h3>{sub_html}',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# COLUMN AUTO-MAPPING  (Change 1)
# ═══════════════════════════════════════════════════════════════════════════

CORE_FIELDS: dict[str, list[str]] = {
    "fan_id": [
        "fan id", "fan_id", "fanid", "customer id", "customer_id",
        "member id", "member_id", "supporter id", "id", "fan number",
    ],
    "membership_category": [
        "membership category", "membership_category", "membership type",
        "membership_type", "member type", "tier", "membership", "category",
    ],
    "engagement_score": [
        "engagement score", "engagement_score", "engagement",
        "eng score", "engagement rating", "engagement index",
    ],
    "commercial_score": [
        "commercial score", "commercial_score", "commercial value",
        "commercial_value", "commercial rating", "commercial index",
    ],
    "loyalty_score": [
        "loyalty score", "loyalty_score", "loyalty",
        "loyalty rating", "loyalty index",
    ],
    "churn_risk": [
        "churn risk", "churn_risk", "churn", "churn probability",
        "churn score", "attrition risk", "lapse risk", "churn rate",
    ],
    "channel_preference": [
        "channel preference", "channel_preference", "preferred channel",
        "communication preference", "contact preference", "channel",
    ],
    "age": [
        "age", "age group", "age_group", "fan age", "age band", "age bracket",
    ],
    "last_purchase_date": [
        "last purchase date", "last_purchase_date", "last purchase",
        "last transaction", "last transaction date", "last bought",
        "last order date", "last activity date",
    ],
    "match_attendance": [
        "match attendance", "match_attendance", "attendance",
        "matches attended", "games attended", "fixtures attended",
        "attendance count", "match count",
    ],
    "segment": [
        "segment", "fan segment", "fan_segment", "cohort",
        "group", "customer segment", "fan group",
    ],
    "fixture_type": [
        "fixture type", "fixture_type", "competition", "match type",
        "competition type", "fixture", "event type",
    ],
}

_HIGH_CONF = 85
_LOW_CONF  = 50


def auto_map_columns(uploaded_cols: list) -> dict:
    """
    Returns {core_field: (best_uploaded_col, score, tier)}
    tier is one of 'auto' | 'low' | 'unmatched'.
    Falls back to simple substring matching if rapidfuzz unavailable.
    """
    norm = {c: c.lower().replace("_", " ").strip() for c in uploaded_cols}
    used: set = set()
    result: dict = {}

    for field, aliases in CORE_FIELDS.items():
        best_col, best_score = None, 0

        for col, col_norm in norm.items():
            if col in used:
                continue
            if HAS_RAPIDFUZZ:
                score = max(rfuzz.ratio(col_norm, a.lower()) for a in aliases)
            else:
                # Simple fallback: check if any alias is a substring
                score = 90 if any(a in col_norm or col_norm in a for a in aliases) else 0

            if score > best_score:
                best_score = score
                best_col = col

        if best_score >= _HIGH_CONF:
            result[field] = (best_col, best_score, "auto")
            used.add(best_col)
        elif best_score >= _LOW_CONF:
            result[field] = (best_col, best_score, "low")
        else:
            result[field] = (None, best_score, "unmatched")

    return result


# ═══════════════════════════════════════════════════════════════════════════
# DATA STANDARDISATION
# ═══════════════════════════════════════════════════════════════════════════

def _age_band(val) -> str:
    try:
        a = int(float(val))
        if a < 18:  return "Under 18"
        if a < 25:  return "18-24"
        if a < 35:  return "25-34"
        if a < 45:  return "35-44"
        if a < 55:  return "45-54"
        if a < 65:  return "55-64"
        return "65+"
    except Exception:
        return str(val)


def _compute_segments(df: pd.DataFrame) -> pd.Series:
    """Assign a segment to each fan from available score columns."""
    has_churn = "churn_risk" in df.columns
    has_eng   = "engagement_score" in df.columns
    has_mem   = "membership_category" in df.columns
    has_lpd   = "last_purchase_date" in df.columns

    segs = []
    for _, row in df.iterrows():
        churn = float(row["churn_risk"])       if has_churn else 50
        eng   = float(row["engagement_score"]) if has_eng   else 50
        mem_cat = str(row.get("membership_category", "")).lower()
        is_member = any(k in mem_cat for k in ["member", "season", "life", "full", "annual"])

        days_stale = 0
        if has_lpd:
            try:
                d = pd.to_datetime(row["last_purchase_date"])
                days_stale = (datetime.now() - d).days
            except Exception:
                days_stale = 0

        if churn >= 80 or days_stale >= 365:
            segs.append("Win Back")
        elif not is_member and (churn >= 60 or days_stale >= 180):
            segs.append("Dormant")
        elif is_member and churn < 35:
            segs.append("Loyal Members")
        elif eng >= 65 and churn < 55 and not is_member:
            segs.append("High Potential")
        else:
            segs.append("Casual")

    return pd.Series(segs, index=df.index)


def standardise_df(raw: pd.DataFrame, confirmed: dict) -> pd.DataFrame:
    """
    Rename uploaded columns to core field names, coerce numeric types,
    compute segment if missing, add age_group column.
    confirmed: {core_field: uploaded_col | None}
    """
    df = raw.copy()

    rename = {}
    for field, col in confirmed.items():
        if col and col in df.columns and col != field:
            rename[col] = field
    df = df.rename(columns=rename)

    for num_col in ["engagement_score", "commercial_score", "loyalty_score",
                    "churn_risk", "match_attendance"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0)

    if "segment" not in df.columns:
        df["segment"] = _compute_segments(df)

    if "age" in df.columns and "age_group" not in df.columns:
        df["age_group"] = df["age"].apply(_age_band)

    return df


# ═══════════════════════════════════════════════════════════════════════════
# UPLOAD TAB  (Change 1)
# ═══════════════════════════════════════════════════════════════════════════

def render_upload() -> None:
    st.markdown(
        '<h1 style="font-family:\'Syne\',sans-serif;font-size:32px;font-weight:800;'
        'color:#c8f135;margin-bottom:4px">FootIntel</h1>'
        '<p style="color:#6b7280;font-size:13px;margin-bottom:24px">'
        'Fan Intelligence Platform — upload your fan data to begin.</p>',
        unsafe_allow_html=True,
    )

    col_form, col_tip = st.columns([2, 1])

    with col_form:
        club = st.text_input(
            "Club Name",
            value=st.session_state.get("fi_club", ""),
            placeholder="e.g. Arsenal Women FC",
            help="Used throughout templates and reports.",
        )
        if club:
            st.session_state["fi_club"] = club

        uploaded = st.file_uploader(
            "Upload Fan Data CSV",
            type=["csv"],
            help="One row per fan. The more columns you include, the richer the analysis.",
        )

    with col_tip:
        st.markdown(
            card(
                '<span style="color:#c8a800;font-size:11px;font-weight:600">'
                'MINIMUM REQUIRED</span><br>'
                '<span style="color:#9ca3af;font-size:11px;line-height:1.9">'
                '&bull; Fan ID<br>&bull; Membership Category<br>'
                '&bull; Engagement Score<br>&bull; Churn Risk<br>'
                '&bull; Commercial Score</span>'
            ),
            unsafe_allow_html=True,
        )

    if uploaded is None:
        return

    try:
        raw_df = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        return

    uploaded_cols = list(raw_df.columns)
    mapping_result = auto_map_columns(uploaded_cols)  # {field: (col, score, tier)}

    st.markdown("---")
    st.markdown(
        '<h3 style="font-family:\'Syne\',sans-serif;color:#e5e7eb;font-size:18px">'
        'Confirm Column Mapping</h3>'
        '<p style="color:#6b7280;font-size:12px;margin-bottom:16px">'
        'We auto-detected your columns. Review and confirm before proceeding.</p>',
        unsafe_allow_html=True,
    )

    auto_fields    = {f: v for f, v in mapping_result.items() if v[2] == "auto"}
    low_fields     = {f: v for f, v in mapping_result.items() if v[2] == "low"}
    unmatch_fields = {f: v for f, v in mapping_result.items() if v[2] == "unmatched"}

    avail_opts = ["— Not Available —"] + uploaded_cols
    confirmed_mapping: dict = {}

    # ── Section 1: Auto Matched (green) ──
    if auto_fields:
        st.markdown(
            '<div style="background:#052e16;border:1px solid #166534;border-radius:8px;'
            'padding:12px 18px;margin-bottom:10px">'
            '<span style="color:#22c55e;font-size:11px;font-weight:600">'
            f'&#10003; AUTO MATCHED</span>'
            '<span style="color:#4b5563;font-size:10px;margin-left:10px">'
            f'High confidence &mdash; {len(auto_fields)} field(s)</span></div>',
            unsafe_allow_html=True,
        )
        for field, (col, score, _) in auto_fields.items():
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.markdown(
                    f'<div style="color:#22c55e;font-size:12px;padding:8px 0">'
                    f'<strong>{field.replace("_", " ").title()}</strong></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                idx = avail_opts.index(col) if col in avail_opts else 0
                sel = st.selectbox(
                    f"_auto_{field}", avail_opts, index=idx,
                    label_visibility="collapsed", key=f"map_auto_{field}",
                )
            with c3:
                st.markdown(
                    f'<div style="color:#22c55e;font-size:11px;padding:8px 0">'
                    f'{score:.0f}% match</div>',
                    unsafe_allow_html=True,
                )
            confirmed_mapping[field] = sel if sel != "— Not Available —" else None

    # ── Section 2: Low Confidence (amber) ──
    if low_fields:
        st.markdown(
            '<div style="background:#1c1500;border:1px solid #92400e;border-radius:8px;'
            'padding:12px 18px;margin-bottom:10px;margin-top:6px">'
            '<span style="color:#f59e0b;font-size:11px;font-weight:600">'
            '&#9888; LOW CONFIDENCE</span>'
            '<span style="color:#4b5563;font-size:10px;margin-left:10px">'
            f'Please confirm &mdash; {len(low_fields)} field(s)</span></div>',
            unsafe_allow_html=True,
        )
        for field, (col, score, _) in low_fields.items():
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.markdown(
                    f'<div style="color:#f59e0b;font-size:12px;padding:8px 0">'
                    f'<strong>{field.replace("_", " ").title()}</strong></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                idx = avail_opts.index(col) if col and col in avail_opts else 0
                sel = st.selectbox(
                    f"_low_{field}", avail_opts, index=idx,
                    label_visibility="collapsed", key=f"map_low_{field}",
                )
            with c3:
                st.markdown(
                    f'<div style="color:#f59e0b;font-size:11px;padding:8px 0">'
                    f'{score:.0f}% match</div>',
                    unsafe_allow_html=True,
                )
            confirmed_mapping[field] = sel if sel != "— Not Available —" else None

    # ── Section 3: Unmatched Core Fields (red) ──
    if unmatch_fields:
        st.markdown(
            '<div style="background:#1f0a0a;border:1px solid #991b1b;border-radius:8px;'
            'padding:12px 18px;margin-bottom:10px;margin-top:6px">'
            '<span style="color:#ef4444;font-size:11px;font-weight:600">'
            '&#10007; UNMATCHED CORE FIELDS</span>'
            '<span style="color:#4b5563;font-size:10px;margin-left:10px">'
            f'Assign manually or mark not available &mdash; {len(unmatch_fields)} field(s)</span></div>',
            unsafe_allow_html=True,
        )
        for field, _ in unmatch_fields.items():
            c1, c2 = st.columns([2, 3])
            with c1:
                st.markdown(
                    f'<div style="color:#ef4444;font-size:12px;padding:8px 0">'
                    f'<strong>{field.replace("_", " ").title()}</strong></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                sel = st.selectbox(
                    f"_unmatched_{field}", avail_opts, index=0,
                    label_visibility="collapsed", key=f"map_unmatched_{field}",
                )
            confirmed_mapping[field] = sel if sel != "— Not Available —" else None

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("✓ Confirm Mapping and Analyse Fans", key="confirm_mapping_btn"):
        final_df = standardise_df(raw_df, confirmed_mapping)
        st.session_state["fi_df"]               = final_df
        st.session_state["fi_confirmed_mapping"] = confirmed_mapping
        # Force navigation to Fan Dashboard on next render
        st.session_state["fi_nav"] = "📊 Fan Dashboard"
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# HOW TO USE TAB  (Change 4)
# ═══════════════════════════════════════════════════════════════════════════

_STEPS = [
    (
        "Prepare Your Data",
        "Your CSV needs fan-level data with one row per fan. "
        "The more columns you include, the richer your analysis will be. "
        "At minimum you need a Fan ID, Membership Category, and some engagement or purchase history.",
    ),
    (
        "Upload and Confirm Mapping",
        "Upload your CSV and the platform will automatically detect and map your columns. "
        "Review the auto-matched fields, confirm any amber ones, and assign any red ones manually. "
        "Hit Confirm Mapping and Analyse Fans to proceed.",
    ),
    (
        "Understand Your Fan Dashboard",
        "Your dashboard shows how your fanbase splits across five segments and scores every fan "
        "across Engagement, Commercial, Loyalty, Churn Risk, and Conversion. "
        "Start here to get the big picture.",
    ),
    (
        "Identify Your At-Risk Fans",
        "Go to Membership Intelligence to see your Renewal Risk Panel. "
        "These are the fans most likely to lapse in the next 90 days, ranked by churn risk score. "
        "This is your weekly action list.",
    ),
    (
        "Build Your Sponsorship Pitch",
        "Go to Sponsorship Intelligence and scroll to the Sponsor Category Recommendations. "
        "Download the Sponsorship Deck PDF and take it directly into your next sponsor conversation.",
    ),
    (
        "Export and Act",
        "Use the Campaign Generator on the Fan Dashboard to download a targeted fan list "
        "and a ready-to-use email template for any segment. "
        "Upload the fan list to your CRM and send the email. Done.",
    ),
]


def render_how_to_use() -> None:
    st.markdown(
        '<h2 style="font-family:\'Syne\',sans-serif;color:#e5e7eb;font-size:26px;'
        'font-weight:800;margin-bottom:4px">How To Use FootIntel</h2>'
        '<p style="color:#6b7280;font-size:13px;margin-bottom:28px">'
        'A step-by-step guide written for marketing managers.</p>',
        unsafe_allow_html=True,
    )

    for i, (title, body) in enumerate(_STEPS, 1):
        st.markdown(
            f'<div style="display:flex;gap:20px;align-items:flex-start;'
            f'background:#13161d;border:1px solid #2a2f3d;border-radius:10px;'
            f'padding:20px 22px;margin-bottom:12px">'
            f'<div style="min-width:38px;height:38px;background:#c8a800;'
            f'border-radius:50%;display:flex;align-items:center;justify-content:center;'
            f'font-family:\'Syne\',sans-serif;font-weight:800;color:#0a0c10;'
            f'font-size:16px;flex-shrink:0">{i}</div>'
            f'<div>'
            f'<div style="font-family:\'Syne\',sans-serif;font-weight:700;'
            f'color:#e5e7eb;font-size:15px;margin-bottom:6px">{title}</div>'
            f'<div style="color:#9ca3af;font-size:12px;line-height:1.75">{body}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="background:#052e16;border:1px solid #166534;border-radius:10px;'
        'padding:16px 22px;margin-top:16px;text-align:center">'
        '<span style="color:#22c55e;font-size:13px">'
        'Need help or want to connect your own data? '
        'Built by <strong>Kush Savant</strong>, MSc Sports Analytics, '
        'Loughborough University London.</span></div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# SEGMENT COLOURS + EMAIL TEMPLATES  (Change 3)
# ═══════════════════════════════════════════════════════════════════════════

SEG_COLORS = {
    "Loyal Members":  "#c8f135",
    "High Potential": "#3b82f6",
    "Casual":         "#f59e0b",
    "Dormant":        "#6b7280",
    "Win Back":       "#ef4444",
}

_EMAIL_TEMPLATES: dict[str, callable] = {
    "Win Back": lambda club: f"""Subject: We miss you at {club}

Hi [First Name],

It's been a while since we last saw you, and we wanted to reach out personally.

As someone who has supported {club}, you're part of our community — and we'd love to welcome you back.

This season has been one of our most exciting yet. We've got big fixtures on the horizon and we don't want you to miss them.

As a thank you for your past support, we'd like to offer you an exclusive discount:

Use code MISSYOU20 for 20% off your next ticket purchase at {club}.

Come back and remind yourself why you love {club}.

Warm regards,
{club} Fan Engagement Team""",

    "Dormant": lambda club: f"""Subject: It's been a while — we'd love to see you at {club}

Hi [First Name],

We noticed you haven't been to see us in a while, and we miss having you in the stands.

Life gets busy — we completely understand. But we wanted to make sure you hadn't lost touch with your club.

We're offering a special Welcome Back package for returning fans — a pair of tickets to any home fixture this season at half price.

Reply to this email or contact our fan services team to claim your offer.

We'd love to see your face back in the crowd at {club}.

{club} Fan Engagement Team""",

    "High Potential": lambda club: f"""Subject: Your next step with {club}

Hi [First Name],

You're one of our most engaged fans — and we think it's time to make it official.

Becoming a member of {club} isn't just about watching matches. It's about being part of something bigger: early access to tickets, exclusive member events, priority seating, and a direct connection to your club.

We're currently offering a new member trial — join today and your first month is on us.

Visit our membership page or reply to this email to start your membership journey.

You're already a huge part of our community. It's time to make it count.

{club} Membership Team""",

    "Casual": lambda club: f"""Subject: Make your mark at {club} this season

Hi [First Name],

Every great fan story starts with showing up more often — and we'd love for you to be part of ours this season.

Whether it's bringing a friend, getting to more home matches, or getting involved in our fan community, there's a place for you here at {club}.

We've put together multi-match bundles so you can plan your season and save at the same time.

Check out our current match bundle offers and make this your best season yet.

The atmosphere is electric when our stands are full — and you're a part of that.

{club} Fan Engagement Team""",

    "Loyal Members": lambda club: f"""Subject: Thank you for your loyalty to {club}

Hi [First Name],

We don't say it often enough — but thank you. Your loyal support means everything to this club.

As one of our most valued members, you'll be the first to know: we're launching our Early Access programme for the upcoming season. As a loyal member, you get:

- Priority ticket selection before general release
- An exclusive member gift delivered to your door
- An invitation to our pre-season member event

You've stood with us through everything. We want to make sure you feel that loyalty returned.

Your exclusive Early Access window opens soon. Watch your inbox.

With gratitude,
{club} Club Management""",
}


# ═══════════════════════════════════════════════════════════════════════════
# FAN DASHBOARD TAB  (Change 2 insight + Change 3 Campaign Generator)
# ═══════════════════════════════════════════════════════════════════════════

def _fan_dashboard_insight(df: pd.DataFrame) -> tuple[str, str]:
    seg_counts  = df["segment"].value_counts()
    biggest_seg = seg_counts.idxmax()
    biggest_n   = int(seg_counts.max())

    if "churn_risk" in df.columns:
        avg_churn = df[df["segment"] == biggest_seg]["churn_risk"].mean()
        s1 = (
            f"{biggest_n:,} of your fans are in the {biggest_seg} segment "
            f"with an average churn risk of {avg_churn:.0f} — "
            f"your biggest volume risk this period."
        )
    else:
        s1 = (
            f"{biggest_n:,} of your fans are in the {biggest_seg} segment — "
            f"your largest group by volume."
        )

    if "age_group" in df.columns:
        casual = df[df["segment"] == "Casual"]
        if not casual.empty and "churn_risk" in df.columns:
            top_age = casual.groupby("age_group")["churn_risk"].mean().idxmax()
            s2 = (
                f"Focus retention spend on the {top_age} age group "
                f"where Casual fans carry the highest average churn risk."
            )
        else:
            top_age = df["age_group"].value_counts().idxmax()
            s2 = f"Your largest age group is {top_age} — consider targeting them first."
    else:
        s2 = "Add age data to unlock demographic targeting recommendations."

    return s1, s2


def render_fan_dashboard(df: pd.DataFrame, club: str) -> None:
    s1, s2 = _fan_dashboard_insight(df)
    insight_banner(s1, s2)

    # ── KPIs ──
    total    = len(df)
    high_risk = int((df["churn_risk"] > 70).sum()) if "churn_risk" in df.columns else "N/A"
    avg_eng  = f"{df['engagement_score'].mean():.0f}" if "engagement_score" in df.columns else "N/A"
    avg_comm = f"{df['commercial_score'].mean():.0f}" if "commercial_score" in df.columns else "N/A"

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(kpi("Total Fans", f"{total:,}", "in dataset"), unsafe_allow_html=True)
    with k2: st.markdown(kpi("High Churn Risk", f"{high_risk:,}", "churn risk > 70", color="#ef4444"), unsafe_allow_html=True)
    with k3: st.markdown(kpi("Avg Engagement", avg_eng, "out of 100"), unsafe_allow_html=True)
    with k4: st.markdown(kpi("Avg Commercial Score", avg_comm, "out of 100", color="#3b82f6"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Segment donut + scatter/histogram ──
    col_a, col_b = st.columns(2)

    with col_a:
        section_header("Segment Distribution")
        seg_df = df["segment"].value_counts().reset_index()
        seg_df.columns = ["Segment", "Count"]
        fig_donut = px.pie(
            seg_df, names="Segment", values="Count",
            color="Segment", color_discrete_map=SEG_COLORS, hole=0.55,
        )
        fig_donut.update_layout(
            paper_bgcolor="#0a0c10", plot_bgcolor="#0a0c10",
            font_color="#9ca3af", legend_font_size=11,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_donut, use_container_width=True, key="fd_seg_donut")

    with col_b:
        if "engagement_score" in df.columns and "churn_risk" in df.columns:
            section_header("Engagement vs Churn Risk")
            fig_scatter = px.scatter(
                df, x="engagement_score", y="churn_risk",
                color="segment", color_discrete_map=SEG_COLORS, opacity=0.65,
                labels={"engagement_score": "Engagement Score", "churn_risk": "Churn Risk"},
            )
            fig_scatter.update_layout(
                paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                font_color="#9ca3af", legend_font_size=11,
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_scatter, use_container_width=True, key="fd_eng_churn_scatter")
        else:
            score_cols = [c for c in
                          ["engagement_score", "commercial_score", "loyalty_score"]
                          if c in df.columns]
            if score_cols:
                section_header("Score Distributions")
                fig_hist = go.Figure()
                _hcols = ["#c8f135", "#3b82f6", "#f59e0b"]
                for idx, sc in enumerate(score_cols):
                    fig_hist.add_trace(go.Histogram(
                        x=df[sc], name=sc.replace("_", " ").title(),
                        marker_color=_hcols[idx % len(_hcols)],
                        opacity=0.75, nbinsx=20,
                    ))
                fig_hist.update_layout(
                    paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                    font_color="#9ca3af", barmode="overlay",
                    margin=dict(t=10, b=10, l=10, r=10),
                )
                st.plotly_chart(fig_hist, use_container_width=True, key="fd_score_hist")

    # ── Average scores by segment ──
    score_cols = [c for c in
                  ["engagement_score", "commercial_score", "loyalty_score", "churn_risk"]
                  if c in df.columns]
    if score_cols:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Average Scores by Segment")
        seg_means = df.groupby("segment")[score_cols].mean().reset_index()
        fig_bar = go.Figure()
        _bcols = ["#c8f135", "#3b82f6", "#f59e0b", "#ef4444"]
        for idx, sc in enumerate(score_cols):
            fig_bar.add_trace(go.Bar(
                name=sc.replace("_", " ").title(),
                x=seg_means["segment"], y=seg_means[sc],
                marker_color=_bcols[idx % len(_bcols)],
            ))
        fig_bar.update_layout(
            paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
            font_color="#9ca3af", barmode="group", legend_font_size=11,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="fd_seg_score_bar")

    # ══════════════════════════════════════════════════════════════════════
    # CAMPAIGN GENERATOR  (Change 3)
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="border-top:1px solid #2a2f3d;padding-top:24px">'
        '<h3 style="font-family:\'Syne\',sans-serif;color:#e5e7eb;'
        'font-size:18px;margin-bottom:4px">Campaign Generator</h3>'
        '<p style="color:#6b7280;font-size:12px;margin-bottom:16px">'
        'Download a targeted fan list and ready-to-use email template for any segment.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    seg_choice = st.selectbox(
        "Select Segment",
        options=["Win Back", "Dormant", "High Potential", "Casual", "Loyal Members"],
        key="cg_seg_select",
    )

    seg_fans = df[df["segment"] == seg_choice].copy()
    export_cols = [c for c in
                   ["fan_id", "membership_category", "engagement_score",
                    "commercial_score", "churn_risk", "channel_preference"]
                   if c in seg_fans.columns]

    if export_cols:
        csv_bytes = seg_fans[export_cols].to_csv(index=False).encode()
        st.download_button(
            label=f"Download {seg_choice} Fan List ({len(seg_fans):,} fans)",
            data=csv_bytes,
            file_name=f"{club.replace(' ', '_')}_{seg_choice.replace(' ', '_')}_fans.csv",
            mime="text/csv",
            key="cg_download_btn",
        )
    else:
        st.info("No exportable columns found in the mapped data.")

    template_fn  = _EMAIL_TEMPLATES.get(seg_choice)
    template_txt = template_fn(club) if template_fn else ""
    st.text_area(
        "Email Template",
        value=template_txt,
        height=300,
        key="cg_email_template",
    )
    st.caption(
        "Copy the template above, paste into your email platform, "
        "and personalise the [First Name] placeholder."
    )


# ═══════════════════════════════════════════════════════════════════════════
# MEMBERSHIP INTELLIGENCE TAB  (Change 2 insight)
# ═══════════════════════════════════════════════════════════════════════════

def _membership_insight(df: pd.DataFrame) -> tuple[str, str]:
    has_churn = "churn_risk" in df.columns
    has_mem   = "membership_category" in df.columns
    has_lpd   = "last_purchase_date" in df.columns

    high_risk_n = int((df["churn_risk"] > 70).sum()) if has_churn else 0

    if has_mem and has_churn:
        mem_mask = df["membership_category"].str.lower().str.contains(
            "full|life|season|annual", na=False,
        )
        mem_high = int((df[mem_mask]["churn_risk"] > 70).sum())

        if has_lpd:
            try:
                lpd = pd.to_datetime(df["last_purchase_date"], errors="coerce")
                cutoff = datetime.now() - timedelta(days=400)
                stale  = int((lpd[mem_mask.values] < cutoff).sum())
                s1 = (
                    f"{high_risk_n:,} fans are at high churn risk, including "
                    f"{mem_high} Full/Life Members — {stale} of whom have not "
                    f"purchased since early last year."
                )
            except Exception:
                s1 = (
                    f"{high_risk_n:,} fans are at high churn risk, "
                    f"including {mem_high} Full or Life Members."
                )
        else:
            s1 = (
                f"{high_risk_n:,} fans are at high churn risk, "
                f"including {mem_high} members who need immediate attention."
            )
    else:
        s1 = f"{high_risk_n:,} fans have a churn risk score above 70 and need attention."

    s2 = (
        "Personal outreach to these members this week "
        "could protect significant annual membership revenue."
    )
    return s1, s2


def render_membership_intel(df: pd.DataFrame, club: str) -> None:
    s1, s2 = _membership_insight(df)
    insight_banner(s1, s2)

    # ── Renewal Risk Panel ──
    section_header("Renewal Risk Panel", "Fans most likely to lapse — sorted by churn risk")

    if "churn_risk" in df.columns:
        risk_df = df.sort_values("churn_risk", ascending=False).head(50)
        disp = [c for c in
                ["fan_id", "membership_category", "engagement_score",
                 "commercial_score", "churn_risk", "channel_preference"]
                if c in risk_df.columns]
        cfg: dict = {}
        if "churn_risk" in disp:
            cfg["churn_risk"] = st.column_config.ProgressColumn(
                "Churn Risk", min_value=0, max_value=100)
        if "engagement_score" in disp:
            cfg["engagement_score"] = st.column_config.ProgressColumn(
                "Engagement", min_value=0, max_value=100)
        if "commercial_score" in disp:
            cfg["commercial_score"] = st.column_config.ProgressColumn(
                "Commercial", min_value=0, max_value=100)
        st.dataframe(risk_df[disp].reset_index(drop=True),
                     use_container_width=True, column_config=cfg)
    else:
        st.info("Upload a churn_risk column to see the Renewal Risk Panel.")

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        section_header("Churn Risk Distribution")
        if "churn_risk" in df.columns:
            fig_churn = px.histogram(
                df, x="churn_risk", nbins=20,
                color="segment", color_discrete_map=SEG_COLORS,
            )
            fig_churn.update_layout(
                paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                font_color="#9ca3af", margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            )
            st.plotly_chart(fig_churn, use_container_width=True, key="mi_churn_hist")
        else:
            st.info("No churn risk data available.")

    with col_b:
        if "membership_category" in df.columns:
            section_header("Membership Category Breakdown")
            mem_cts = df["membership_category"].value_counts().reset_index()
            mem_cts.columns = ["Category", "Count"]
            fig_mem = px.bar(
                mem_cts, x="Count", y="Category", orientation="h",
                color_discrete_sequence=["#c8f135"],
            )
            fig_mem.update_layout(
                paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                font_color="#9ca3af", margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            )
            st.plotly_chart(fig_mem, use_container_width=True, key="mi_mem_bar")
        else:
            st.info("No membership category data available.")

    # ── Segment × Membership heatmap ──
    if "membership_category" in df.columns:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Segment x Membership Heatmap")
        heat = pd.crosstab(df["segment"], df["membership_category"])
        fig_heat = px.imshow(
            heat,
            color_continuous_scale=[[0, "#0a0c10"], [0.5, "#1a3a1a"], [1, "#c8f135"]],
            text_auto=True,
        )
        fig_heat.update_layout(
            paper_bgcolor="#0a0c10", font_color="#9ca3af",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_heat, use_container_width=True, key="mi_seg_mem_heatmap")


# ═══════════════════════════════════════════════════════════════════════════
# SPONSORSHIP INTELLIGENCE TAB  (Change 2 insight)
# ═══════════════════════════════════════════════════════════════════════════

_SPONSOR_CATS: dict[str, list] = {
    "Under 18": ["Gaming", "Energy Drinks", "Music Streaming", "Fast Fashion"],
    "18-24":    ["Energy Drinks", "Gaming", "Fast Fashion", "Music Streaming"],
    "25-34":    ["Financial Services", "Insurance", "Auto", "Travel"],
    "35-44":    ["Financial Services", "Sports Equipment", "Family Brands", "Home & Garden"],
    "45-54":    ["Financial Services", "Healthcare", "Travel", "Premium Auto"],
    "55-64":    ["Healthcare", "Financial Planning", "Travel", "Luxury"],
    "65+":      ["Healthcare", "Financial Planning", "Travel", "Retirement Services"],
}


def _sponsorship_insight(df: pd.DataFrame) -> tuple[str, str]:
    has_age  = "age_group" in df.columns
    has_comm = "commercial_score" in df.columns
    has_mem  = "membership_category" in df.columns

    dom_age = df["age_group"].value_counts().idxmax() if has_age else "35-44"

    if has_comm and has_mem:
        life_mask = df["membership_category"].str.lower().str.contains(
            "life|full", na=False)
        life_comm = df[life_mask]["commercial_score"].mean() if life_mask.any() else 0
        overall   = df["commercial_score"].mean()
        cats      = _SPONSOR_CATS.get(dom_age, ["Financial Services", "Sports Equipment"])
        s1 = (
            f"Your audience skews {dom_age} with Life/Full Member commercial scores "
            f"averaging {life_comm:.0f} — a strong fit for "
            f"{cats[0]} and {cats[1] if len(cats) > 1 else 'Sports Equipment'} partners."
        )
        s2 = (
            f"Your current average commercial score of {overall:.0f} has room to grow "
            f"by converting more High Potential fans to membership."
        )
    elif has_comm:
        avg_comm = df["commercial_score"].mean()
        s1 = (
            f"Your audience skews {dom_age} with an average commercial score "
            f"of {avg_comm:.0f} out of 100."
        )
        s2 = "Segment by engagement tier to identify the highest-value audience for sponsors."
    else:
        s1 = f"Your audience skews {dom_age} — a key demographic for major brand partners."
        s2 = "Add commercial score data to quantify your sponsorship proposition."

    return s1, s2


def render_sponsorship_intel(df: pd.DataFrame, club: str) -> None:
    s1, s2 = _sponsorship_insight(df)
    insight_banner(s1, s2)

    col_a, col_b = st.columns(2)

    with col_a:
        if "age_group" in df.columns:
            section_header("Audience Age Profile")
            age_cts = df["age_group"].value_counts().sort_index().reset_index()
            age_cts.columns = ["Age Group", "Count"]
            fig_age = px.bar(age_cts, x="Age Group", y="Count",
                             color_discrete_sequence=["#3b82f6"])
            fig_age.update_layout(
                paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                font_color="#9ca3af", margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            )
            st.plotly_chart(fig_age, use_container_width=True, key="si_age_bar")
        else:
            st.info("Upload an age or age_group column for audience profiling.")

    with col_b:
        if "commercial_score" in df.columns:
            section_header("Commercial Score by Segment")
            comm_seg = df.groupby("segment")["commercial_score"].mean().reset_index()
            comm_seg.columns = ["Segment", "Avg Commercial Score"]
            fig_comm = px.bar(
                comm_seg, x="Segment", y="Avg Commercial Score",
                color="Segment", color_discrete_map=SEG_COLORS,
            )
            fig_comm.update_layout(
                paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                font_color="#9ca3af", showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            )
            st.plotly_chart(fig_comm, use_container_width=True, key="si_comm_seg_bar")

    # ── Sponsor category recommendations ──
    if "age_group" in df.columns:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Sponsor Category Recommendations",
                       f"Based on your dominant audience age group: {df['age_group'].value_counts().idxmax()}")
        dom_age = df["age_group"].value_counts().idxmax()
        cats    = _SPONSOR_CATS.get(dom_age, ["Sports Equipment", "Financial Services"])
        cols    = st.columns(len(cats))
        for i, cat in enumerate(cats):
            with cols[i]:
                st.markdown(
                    f'<div style="background:#13161d;border:1px solid #2a2f3d;'
                    f'border-radius:8px;padding:14px;text-align:center">'
                    f'<div style="color:#c8a800;font-size:20px">&#127991;</div>'
                    f'<div style="color:#e5e7eb;font-size:12px;font-weight:600;'
                    f'margin-top:6px">{cat}</div></div>',
                    unsafe_allow_html=True,
                )

    # ── Pitch score gauge ──
    if "commercial_score" in df.columns:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Sponsorship Pitch Score")
        pitch = min(100.0, float(df["commercial_score"].mean()) * 1.1)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pitch,
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor="#6b7280"),
                bar=dict(color="#c8f135"),
                bgcolor="#13161d",
                bordercolor="#2a2f3d",
                steps=[
                    dict(range=[0,  40], color="#1f0a0a"),
                    dict(range=[40, 70], color="#1c1500"),
                    dict(range=[70,100], color="#052e16"),
                ],
            ),
            number=dict(suffix="/100", font=dict(color="#c8f135", size=32)),
            title=dict(text="Overall Pitch Score", font=dict(color="#9ca3af", size=13)),
        ))
        fig_gauge.update_layout(
            paper_bgcolor="#0a0c10", font_color="#9ca3af",
            height=260, margin=dict(t=30, b=10, l=30, r=30),
        )
        st.plotly_chart(fig_gauge, use_container_width=True, key="si_pitch_gauge")


# ═══════════════════════════════════════════════════════════════════════════
# MATCH INTELLIGENCE TAB  (Change 2 insight)
# ═══════════════════════════════════════════════════════════════════════════

def _match_insight(df: pd.DataFrame) -> tuple[str, str]:
    has_att     = "match_attendance" in df.columns
    has_comm    = "commercial_score" in df.columns
    has_fixture = "fixture_type" in df.columns
    has_eng     = "engagement_score" in df.columns

    if has_fixture and has_comm:
        best_fix   = df.groupby("fixture_type")["commercial_score"].mean().idxmax()
        loyal_mask = df["segment"] == "Loyal Members"
        loy_fix_df = df[loyal_mask & (df["fixture_type"] == best_fix)]
        loyal_comm = loy_fix_df["commercial_score"].mean() if not loy_fix_df.empty else 0
        s1 = (
            f"{best_fix} drives your highest commercial value fans, "
            f"with Loyal Members averaging a commercial score of {loyal_comm:.0f} "
            f"at these fixtures."
        )
    elif has_comm:
        avg_comm = df["commercial_score"].mean()
        s1 = f"Your average commercial score across all fans is {avg_comm:.0f} out of 100."
    else:
        s1 = "Upload commercial score and fixture data for match-level revenue intelligence."

    if has_eng and has_att:
        high_eng_low_att = int(
            ((df["engagement_score"] > 70) & (df["match_attendance"] < 6)).sum()
        )
        s2 = (
            f"{high_eng_low_att} high-engagement fans attend fewer than 6 matches per season "
            f"and are prime targets for a discounted ticket offer."
        )
    else:
        s2 = "Add match attendance data to identify high-engagement fans who attend infrequently."

    return s1, s2


def render_match_intel(df: pd.DataFrame, club: str) -> None:
    s1, s2 = _match_insight(df)
    insight_banner(s1, s2)

    has_att     = "match_attendance" in df.columns
    has_comm    = "commercial_score" in df.columns
    has_fixture = "fixture_type" in df.columns
    has_eng     = "engagement_score" in df.columns

    col_a, col_b = st.columns(2)

    with col_a:
        if has_att:
            section_header("Match Attendance Distribution")
            fig_att = px.histogram(
                df, x="match_attendance", nbins=20,
                color="segment", color_discrete_map=SEG_COLORS,
            )
            fig_att.update_layout(
                paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                font_color="#9ca3af", margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            )
            st.plotly_chart(fig_att, use_container_width=True, key="mti_att_hist")
        else:
            st.info("Upload match attendance data to see the attendance distribution.")

    with col_b:
        if has_fixture and has_comm:
            section_header("Commercial Score by Fixture Type")
            fix_comm = df.groupby("fixture_type")["commercial_score"].mean().reset_index()
            fix_comm.columns = ["Fixture Type", "Avg Commercial Score"]
            fig_fix = px.bar(fix_comm, x="Fixture Type", y="Avg Commercial Score",
                             color_discrete_sequence=["#c8f135"])
            fig_fix.update_layout(
                paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                font_color="#9ca3af", margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            )
            st.plotly_chart(fig_fix, use_container_width=True, key="mti_fix_comm_bar")
        elif has_comm:
            section_header("Commercial Score by Segment")
            seg_comm = df.groupby("segment")["commercial_score"].mean().reset_index()
            seg_comm.columns = ["Segment", "Avg Commercial Score"]
            fig_sc = px.bar(
                seg_comm, x="Segment", y="Avg Commercial Score",
                color="Segment", color_discrete_map=SEG_COLORS,
            )
            fig_sc.update_layout(
                paper_bgcolor="#0a0c10", plot_bgcolor="#13161d",
                font_color="#9ca3af", showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            )
            st.plotly_chart(fig_sc, use_container_width=True, key="mti_seg_comm_bar")
        else:
            st.info("Add commercial score data to unlock match revenue analysis.")

    # ── High engagement, low attendance target list ──
    if has_eng and has_att:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header(
            "High Engagement, Low Attendance Fans",
            "Engagement score > 70 and fewer than 6 matches attended — prime ticket offer targets",
        )
        target_df = df[
            (df["engagement_score"] > 70) & (df["match_attendance"] < 6)
        ].copy()
        disp = [c for c in
                ["fan_id", "membership_category", "engagement_score",
                 "match_attendance", "churn_risk", "channel_preference"]
                if c in target_df.columns]
        if not target_df.empty and disp:
            tbl_cfg: dict = {}
            if "engagement_score" in disp:
                tbl_cfg["engagement_score"] = st.column_config.ProgressColumn(
                    "Engagement", min_value=0, max_value=100)
            if "churn_risk" in disp:
                tbl_cfg["churn_risk"] = st.column_config.ProgressColumn(
                    "Churn Risk", min_value=0, max_value=100)
            if "match_attendance" in disp:
                tbl_cfg["match_attendance"] = st.column_config.NumberColumn("Matches Attended")
            st.dataframe(
                target_df[disp].sort_values("engagement_score", ascending=False)
                               .reset_index(drop=True),
                use_container_width=True,
                column_config=tbl_cfg,
            )
            csv_bytes = target_df[disp].to_csv(index=False).encode()
            st.download_button(
                "Download Target List",
                data=csv_bytes,
                file_name=f"{club.replace(' ', '_')}_ticket_offer_targets.csv",
                mime="text/csv",
                key="mti_download_targets",
            )
        else:
            st.info("No fans match this profile in the current dataset.")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

_TABS = [
    "📤 Upload",
    "📖 How To Use",
    "📊 Fan Dashboard",
    "🏟 Membership Intelligence",
    "🤝 Sponsorship Intelligence",
    "📅 Match Intelligence",
]
_ANALYSIS_TABS = set(_TABS[2:])


def main() -> None:
    # ── App header ──
    st.markdown(
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">'
        '<span style="font-family:\'Syne\',sans-serif;font-size:22px;font-weight:800;'
        'color:#c8f135">FootIntel</span>'
        '<span style="color:#4b5563;font-size:11px">Fan Intelligence Platform</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    df   = st.session_state.get("fi_df")
    club = st.session_state.get("fi_club", "Your Club")

    # ── Navigation ──
    page = st.radio("nav", _TABS, index=0, key="fi_nav", horizontal=True)
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)

    # Gate analysis tabs behind successful upload
    if page in _ANALYSIS_TABS and df is None:
        st.markdown(
            card(
                '<span style="color:#f59e0b">&#9888; No data loaded. '
                "Please upload your fan data on the Upload tab first.</span>"
            ),
            unsafe_allow_html=True,
        )
        return

    if   page == "📤 Upload":
        render_upload()
    elif page == "📖 How To Use":
        render_how_to_use()
    elif page == "📊 Fan Dashboard":
        render_fan_dashboard(df, club)
    elif page == "🏟 Membership Intelligence":
        render_membership_intel(df, club)
    elif page == "🤝 Sponsorship Intelligence":
        render_sponsorship_intel(df, club)
    elif page == "📅 Match Intelligence":
        render_match_intel(df, club)


if __name__ == "__main__":
    main()
