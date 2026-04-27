import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from data import get_full_club_data, get_claude_recommendation, WSL_CLUBS, WSL_LEAGUE_CONTEXT, PLAYER_DATA

st.set_page_config(page_title="WSL Fan Intelligence",
    page_icon="⚽", layout="wide", initial_sidebar_state="collapsed")

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
div[data-testid="stButton"]>button:hover{
    border-color:#c8f135!important;color:#c8f135!important;}

/* ── Mobile responsive ── */
@media (max-width: 768px) {
    .block-container{padding:1rem!important;}
    [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;}
    [data-testid="column"]{
        min-width:100%!important;
        flex:1 1 100%!important;
    }
    div[data-testid="stRadio"]>div>label{
        flex:1 1 calc(50% - 8px)!important;
        text-align:center!important;
        padding:8px 10px!important;
    }
}
@media (max-width: 480px) {
    div[data-testid="stRadio"]>div>label{
        flex:1 1 100%!important;
    }
}
</style>
""", unsafe_allow_html=True)

def card(content, padding="16px 18px", bg="#13161d", border="#2a2f3d", radius="10px"):
    return f'<div style="background:{bg};border:1px solid {border};border-radius:{radius};padding:{padding};margin-bottom:14px">{content}</div>'

def kpi_html(label, value, delta, color="#c8f135", delta_color="#22c55e", sub_delta=None):
    sub = f'<div style="font-size:10px;color:#4b5563;margin-top:2px">{sub_delta}</div>' if sub_delta else ""
    return f"""
    <div style="background:#13161d;border:1px solid #1f2937;border-radius:10px;padding:18px 20px;height:100%">
        <div style="font-size:10px;color:#6b7280;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">{label}</div>
        <div style="font-family:'Syne',sans-serif;font-size:34px;font-weight:800;color:{color};line-height:1">{value}</div>
        <div style="font-size:11px;color:{delta_color};margin-top:6px">{delta}</div>
        {sub}
    </div>"""

def risk_badge(level):
    colors = {"HIGH":"#ef4444","MED":"#f59e0b","LOW":"#22c55e","OPT":"#3d9cf0"}
    bg = {"HIGH":"#1f0a0a","MED":"#1c1500","LOW":"#0a1f0a","OPT":"#0a1020"}
    c = colors.get(level,"#6b7280")
    b = bg.get(level,"#13161d")
    return f'<span style="background:{b};color:{c};border:1px solid {c};font-size:9px;padding:2px 7px;border-radius:8px;float:right;margin-left:8px">{level}</span>'

def form_pill(result):
    colors = {"W":"#22c55e","D":"#f59e0b","L":"#ef4444"}
    bg = {"W":"#052e16","D":"#1c1500","L":"#1f0a0a"}
    c = colors.get(result,"#6b7280")
    b = bg.get(result,"#13161d")
    return f'<span style="background:{b};color:{c};border:1px solid {c};font-size:11px;font-weight:600;padding:3px 9px;border-radius:5px;margin-right:4px">{result}</span>'

def form_pill_comp(result, comp):
    """Result pill with competition label underneath."""
    colors = {"W":"#22c55e","D":"#f59e0b","L":"#ef4444"}
    bg     = {"W":"#052e16","D":"#1c1500","L":"#1f0a0a"}
    comp_c = {"WSL":"#6b7280","FAC":"#f59e0b","UCL":"#3d9cf0"}
    c = colors.get(result,"#6b7280")
    b = bg.get(result,"#13161d")
    cc = comp_c.get(comp,"#6b7280")
    return (
        f'<div style="display:inline-block;text-align:center;margin-right:6px;vertical-align:top">'
        f'<span style="background:{b};color:{c};border:1px solid {c};font-size:11px;font-weight:600;'
        f'padding:3px 9px;border-radius:5px;display:block">{result}</span>'
        f'<div style="font-size:8px;color:{cc};margin-top:3px;letter-spacing:.04em">{comp}</div>'
        f'</div>'
    )

# ── Data transparency banner ─────────────────────────────────────────────────
st.markdown("""
<div style="background:#0d1117;border:1px solid #1a1e27;border-radius:8px;padding:7px 16px;margin-bottom:18px;display:flex;align-items:center;justify-content:center;gap:12px">
    <span style="font-size:10px;color:#374151;letter-spacing:.03em">
        <span style="color:#22c55e;font-size:9px">⬤</span> Live data: YouTube &nbsp;·&nbsp;
        <span style="color:#f59e0b;font-size:9px">◯</span> Simulated: Sentiment, Ticketing, Social &nbsp;·&nbsp;
        Built as a proof of concept
    </span>
</div>""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([5,1])
with c1:
    st.markdown("""
    <div style="margin-bottom:4px">
        <span style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#c8f135;letter-spacing:-1px">FanIntel</span>
        <span style="font-family:'Syne',sans-serif;font-size:28px;font-weight:400;color:#4b5563"> / WSL Edition</span>
    </div>
    <div style="font-size:11px;color:#6b7280;letter-spacing:.04em">
        Women's Super League · 2024–25 · Fan Intelligence & Risk Engine
    </div>
    <div style="font-size:11px;color:#4a7a35;font-style:italic;margin-top:5px;letter-spacing:.02em">
        Turning fan behaviour into commercial decisions — in real time
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right;padding-top:14px"><span style="background:#052e16;border:1px solid #166534;color:#22c55e;font-size:11px;padding:5px 14px;border-radius:20px">● Live</span></div>', unsafe_allow_html=True)

st.markdown("<hr style='border-color:#1f2937;margin:14px 0 12px'>", unsafe_allow_html=True)

# ── Club tabs ─────────────────────────────────────────────────────────────────
selected = st.radio("Club", list(WSL_CLUBS.keys()), horizontal=True)
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── Load ──────────────────────────────────────────────────────────────────────
with st.spinner(f"Pulling fan intelligence for {selected}..."):
    d = get_full_club_data(selected)

kpis             = d["kpis"]
sent             = d["sentiment"]
content          = d["content"]
tickets          = d["tickets"]
trend            = d["trend"]
signals          = d["signals"]
risk             = d["risk_data"]
league           = d["league"]
form             = d["form"]
form_comp        = d["form_comp"]
sources          = d["data_sources"]
cohorts          = d["cohorts"]
att_preds        = d["attendance_predictions"]
churn_risks      = d["churn_risks"]
player_influence = d["player_influence"]
sponsor_exposure = d["sponsor_exposure"]

# ── Source legend ─────────────────────────────────────────────────────────────
def pill(label, live):
    if live:
        return f'<span style="background:#052e16;color:#22c55e;border:1px solid #166534;font-size:9px;padding:2px 8px;border-radius:10px;margin-right:5px">⬤ Live · {label}</span>'
    return f'<span style="background:#1c1500;color:#f59e0b;border:1px solid #92400e;font-size:9px;padding:2px 8px;border-radius:10px;margin-right:5px">◯ Sim · {label}</span>'

st.markdown(
    '<span style="font-size:10px;color:#4b5563;margin-right:6px">Sources:</span>'
    + pill("YouTube", sources["content"]=="live")
    + pill("Reddit sentiment", sources["sentiment"]=="live")
    + pill("X / TikTok", False)
    + pill("Ticketing", False),
    unsafe_allow_html=True)
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ── How-to Guide (shown on first visit, dismissed via session state) ───────────
if "guide_dismissed" not in st.session_state:
    st.session_state["guide_dismissed"] = False

if not st.session_state["guide_dismissed"]:
    st.markdown("""
    <div style="background:#0d1117;border:1px solid #c8f13540;border-radius:10px;padding:20px 24px;margin-bottom:4px">
        <div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:#c8f135;margin-bottom:14px;letter-spacing:-.3px">
            ✦ How to use FanIntel WSL
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px">
            <div>
                <div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">What is FanIntel?</div>
                <div style="font-size:11px;color:#6b7280;line-height:1.7">
                    A real-time fan intelligence platform for WSL clubs. It aggregates signals
                    across sentiment, ticketing, content and commercial data to surface actionable
                    insights for club executives and commercial teams.
                </div>
            </div>
            <div>
                <div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Club selector</div>
                <div style="font-size:11px;color:#6b7280;line-height:1.7">
                    Use the tab selector above to switch between WSL clubs — the dashboard refreshes
                    instantly. The Commercial Impact Summary at the top gives the executive view.
                    Scroll down for deeper data layers including attendance predictions and churn risk.
                </div>
            </div>
            <div>
                <div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Key metric scales</div>
                <div style="font-size:11px;color:#6b7280;line-height:1.8">
                    <span style="color:#9ca3af">FanIntel Score</span> — 0 to 100 &nbsp;·&nbsp; 70+ = healthy<br>
                    <span style="color:#9ca3af">Sentiment Score</span> — 0 to 100 &nbsp;·&nbsp; &gt;65 = above league avg<br>
                    <span style="color:#9ca3af">Ticket Demand</span> — 0 to 1 &nbsp;·&nbsp; 1.0 = sold out<br>
                    <span style="color:#9ca3af">Fan Risk Score</span> — 0 to 100 &nbsp;·&nbsp; lower is better
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    _g_spacer, _g_btn = st.columns([10, 1])
    with _g_btn:
        if st.button("Dismiss ✕", key="dismiss_guide"):
            st.session_state["guide_dismissed"] = True
            st.rerun()
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── FanIntel Composite Score ───────────────────────────────────────────────────
_sentiment_c = kpis["sentiment_score"] * 0.30
_ticket_c    = kpis["demand_index"] * 100 * 0.25
_risk_c      = (100 - kpis["overall_risk"]) * 0.20
_content_c   = min(100, content["engagement_rate"] * 8) * 0.15
_cohort_avg  = sum(100 - c["risk_score"] for c in cohorts) / len(cohorts) if cohorts else 50
_cohort_c    = _cohort_avg * 0.10
fanIntel_score = round(_sentiment_c + _ticket_c + _risk_c + _content_c + _cohort_c)
fi_color = "#22c55e" if fanIntel_score >= 70 else "#f59e0b" if fanIntel_score >= 50 else "#ef4444"
fi_bg    = "#0a1f0a" if fanIntel_score >= 70 else "#1c1500" if fanIntel_score >= 50 else "#1f0a0a"
fi_label = "Strong fan & commercial health" if fanIntel_score >= 70 else "Moderate — action areas identified" if fanIntel_score >= 50 else "At risk — intervention required"
fi_components = [
    ("Sentiment",    f"{kpis['sentiment_score']}/100",   "30%"),
    ("Ticket demand",f"{round(kpis['demand_index']*100)}%", "25%"),
    ("Risk (inv.)",  f"{round(100-kpis['overall_risk'])}", "20%"),
    ("Content eng.", f"{round(min(100, content['engagement_rate']*8))}", "15%"),
    ("Cohort health",f"{round(_cohort_avg)}", "10%"),
]
fi_border = fi_color + "40"
comp_html = "".join(
    '<div style="text-align:center;padding:0 12px;border-right:1px solid #1f2937">'
    + f'<div style="font-size:9px;color:#4b5563;margin-bottom:2px">{lbl}</div>'
    + f'<div style="font-size:12px;font-weight:600;color:#6b7280">{val}</div>'
    + f'<div style="font-size:9px;color:#374151">w:{w}</div>'
    + '</div>'
    for lbl, val, w in fi_components
)
fi_html = (
    f'<div style="background:{fi_bg};border:1px solid {fi_border};border-radius:12px;padding:18px 24px;margin-bottom:18px;display:flex;align-items:center;gap:24px">'
    + f'<div style="flex-shrink:0;text-align:center;min-width:100px">'
    + f'<div style="font-size:9px;color:{fi_color};letter-spacing:.1em;margin-bottom:4px;text-transform:uppercase">FanIntel Score</div>'
    + f'<div style="font-family:Syne,sans-serif;font-size:56px;font-weight:800;color:{fi_color};line-height:1">{fanIntel_score}</div>'
    + '<div style="font-size:10px;color:#4b5563;margin-top:2px">out of 100</div>'
    + '</div>'
    + '<div style="flex:1">'
    + f'<div style="font-size:12px;color:{fi_color};font-weight:500;margin-bottom:6px">{fi_label}</div>'
    + f'<div style="background:#0a0c10;border-radius:5px;height:6px;overflow:hidden;margin-bottom:12px">'
    + f'<div style="width:{fanIntel_score}%;height:100%;background:{fi_color};border-radius:5px"></div>'
    + '</div>'
    + '<div style="font-size:9px;color:#4b5563;margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em">Overall Fan &amp; Commercial Health · Composite of all signals</div>'
    + f'<div style="display:flex;flex-wrap:wrap">{comp_html}</div>'
    + '</div>'
    + '</div>'
)
st.markdown(fi_html, unsafe_allow_html=True)

# ── Commercial Impact Summary (exec view — sits above the data layers) ─────────
st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:12px">Commercial Impact Summary · signal cascade</div>', unsafe_allow_html=True)

# Build the chain dynamically from loaded data
_sent_delta   = kpis["sentiment_score"] - 65
_sent_dir     = "up" if _sent_delta >= 0 else "down"
_sent_node_c  = "#22c55e" if _sent_delta >= 0 else "#ef4444"
_sent_node_bg = "#0a1f0a" if _sent_delta >= 0 else "#1f0a0a"
_sent_txt     = f"Sentiment {_sent_dir} {'+' if _sent_delta>=0 else ''}{_sent_delta} vs league avg"
_sent_sub     = f"Score: {kpis['sentiment_score']}/100"

_dem_pct   = round(kpis["demand_index"] * 100)
_dem_label = "Strong" if _dem_pct >= 75 else "Average" if _dem_pct >= 58 else "Below target"
_dem_c     = "#22c55e" if _dem_pct >= 75 else "#f59e0b" if _dem_pct >= 58 else "#ef4444"
_dem_bg    = "#0a1f0a" if _dem_pct >= 75 else "#1c1500" if _dem_pct >= 58 else "#1f0a0a"
_dem_txt   = f"Ticket demand {_dem_label.lower()}"
_dem_sub   = f"Avg fill: {_dem_pct}%"

_sp_fixtures = sponsor_exposure.get("fixtures", [])
_top_sp    = max(_sp_fixtures, key=lambda x: x["sponsor_index"]) if _sp_fixtures else None
_sp_idx    = _top_sp["sponsor_index"] if _top_sp else 0
_sp_label  = "Elevated" if _sp_idx >= 70 else "Moderate" if _sp_idx >= 50 else "Low"
_sp_c      = "#c8f135" if _sp_idx >= 70 else "#3d9cf0" if _sp_idx >= 50 else "#6b7280"
_sp_bg     = "#0f1a08" if _sp_idx >= 70 else "#0a1020" if _sp_idx >= 50 else "#13161d"
_sp_txt    = f"Sponsor exposure {_sp_label.lower()}"
_sp_sub    = f"Peak index: {_sp_idx}" + (" · DERBY" if _top_sp and _top_sp.get("is_rival") else "")

# Best action: first HIGH signal, else first signal, else fallback
_best_signal  = next((s for s in signals if s["priority"]=="HIGH"), signals[0] if signals else None)
_action_title = _best_signal["action"] if _best_signal else "Review fan intelligence data"
_action_why   = _best_signal["title"] if _best_signal else ""
_action_c     = "#c8f135"
_action_bg    = "#0f1a08"

# Build narrative sentence
_narrative = (
    f"{_sent_txt} · {_dem_txt} at {_dem_pct}% avg capacity · "
    f"Sponsor exposure {_sp_label.lower()} (peak index {_sp_idx}) · "
    f"Action: {_action_title}"
)

_sent_border  = _sent_node_c + "40"
_dem_border   = _dem_c + "40"
_sp_border    = _sp_c + "40"
_action_why_s = _action_why[:60] + ("..." if len(_action_why) > 60 else "")
_arrow = '<div style="display:flex;align-items:center;padding:0 6px;color:#374151;font-size:20px;flex-shrink:0">&#8250;</div>'
cascade_html = (
    '<div style="background:#13161d;border:1px solid #1f2937;border-radius:10px;padding:16px 20px">'
    + '<div style="display:flex;align-items:stretch;gap:0;flex-wrap:wrap;margin-bottom:14px">'
    + f'<div style="background:{_sent_node_bg};border:1px solid {_sent_border};border-radius:8px 0 0 8px;padding:12px 16px;flex:1;min-width:120px">'
    + f'<div style="font-size:8px;color:{_sent_node_c};letter-spacing:.08em;margin-bottom:5px;text-transform:uppercase">Sentiment Score</div>'
    + f'<div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:{_sent_node_c}">{_sent_txt}</div>'
    + f'<div style="font-size:10px;color:#4b5563;margin-top:2px">{_sent_sub}</div>'
    + '</div>'
    + _arrow
    + f'<div style="background:{_dem_bg};border:1px solid {_dem_border};padding:12px 16px;flex:1;min-width:120px">'
    + f'<div style="font-size:8px;color:{_dem_c};letter-spacing:.08em;margin-bottom:5px;text-transform:uppercase">Ticket Demand</div>'
    + f'<div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:{_dem_c}">{_dem_label}</div>'
    + f'<div style="font-size:10px;color:#4b5563;margin-top:2px">{_dem_sub}</div>'
    + '</div>'
    + _arrow
    + f'<div style="background:{_sp_bg};border:1px solid {_sp_border};padding:12px 16px;flex:1;min-width:120px">'
    + f'<div style="font-size:8px;color:{_sp_c};letter-spacing:.08em;margin-bottom:5px;text-transform:uppercase">Sponsor Exposure</div>'
    + f'<div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:{_sp_c}">{_sp_label}</div>'
    + f'<div style="font-size:10px;color:#4b5563;margin-top:2px">{_sp_sub}</div>'
    + '</div>'
    + _arrow
    + f'<div style="background:{_action_bg};border:1px solid {_action_c};border-radius:0 8px 8px 0;padding:12px 16px;flex:1.4;min-width:160px">'
    + f'<div style="font-size:8px;color:{_action_c};letter-spacing:.08em;margin-bottom:5px;text-transform:uppercase">Recommended Action</div>'
    + f'<div style="font-size:12px;font-weight:500;color:#e8eaf0;line-height:1.4">{_action_title}</div>'
    + f'<div style="font-size:10px;color:#4b5563;margin-top:3px;line-height:1.4">{_action_why_s}</div>'
    + '</div>'
    + '</div>'
    + f'<div style="font-size:10px;color:#374151;font-style:italic;border-top:1px solid #1a1e27;padding-top:10px">&#8618; {_narrative}</div>'
    + '</div>'
)
st.markdown(cascade_html, unsafe_allow_html=True)
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5 = st.columns(5)
sent_dir = "up" if kpis["sentiment_score"] >= 65 else "down"
risk_color = "#ef4444" if kpis["overall_risk"] >= 60 else "#f59e0b" if kpis["overall_risk"] >= 35 else "#22c55e"

# Sentiment vs 30 days ago
score_now = kpis["sentiment_score"]
score_30d = sent.get("score_30d_ago", score_now)
delta_30d = score_now - score_30d
delta_30d_str = f"{'▲' if delta_30d >= 0 else '▼'} {abs(delta_30d):+d} vs 30 days ago"
delta_30d_color = "#22c55e" if delta_30d >= 0 else "#ef4444"

with k1: st.markdown(kpi_html(
    "Sentiment Score", score_now,
    f"{'▲' if sent_dir=='up' else '▼'} {score_now-65:+d} vs league avg",
    "#c8f135", "#22c55e" if sent_dir=="up" else "#ef4444",
    sub_delta=f'<span style="color:{delta_30d_color}">{delta_30d_str}</span>',
), unsafe_allow_html=True)
with k2: st.markdown(kpi_html("Content Reach", kpis["content_reach"],
    "— YouTube · last 6 videos", "#e8eaf0", "#6b7280"), unsafe_allow_html=True)
with k3: st.markdown(kpi_html("Ticket Demand", kpis["demand_index"],
    f"{'▲ Strong' if kpis['demand_index']>=.8 else '— Average' if kpis['demand_index']>=.65 else '▼ Below avg'}",
    "#e8eaf0", "#22c55e" if kpis["demand_index"]>=.75 else "#f59e0b",
    sub_delta="0 – 1 scale &nbsp;·&nbsp; 0 = no demand, 1 = sold out"), unsafe_allow_html=True)
with k4: st.markdown(kpi_html("Fan Risk Score", f"{kpis['overall_risk']}/100",
    f"{'🔴 High risk' if kpis['overall_risk']>=60 else '🟡 Medium risk' if kpis['overall_risk']>=35 else '🟢 Low risk'}",
    risk_color, risk_color,
    sub_delta="0 – 100 &nbsp;·&nbsp; lower is better"), unsafe_allow_html=True)
with k5:
    pos = league.get("position","—")
    pts = league.get("pts","—")
    st.markdown(kpi_html("League Position", f"#{pos}",
        f"— {pts} pts · {' '.join(form)}", "#e8eaf0", "#6b7280"), unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Row 1: Sentiment + Risk Engine ───────────────────────────────────────────
col1, col2 = st.columns([3,2])

with col1:
    st.markdown(f'<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:10px">Cross-channel sentiment · 14 days</div>', unsafe_allow_html=True)
    colors_map = {"twitter":"#3d9cf0","instagram":"#c8f135","youtube":"#f59e0b","reddit":"#ef4444"}
    dashes_map = {"twitter":"solid","instagram":"solid","youtube":"dash","reddit":"dot"}
    fig = go.Figure()
    for ch,col in colors_map.items():
        fig.add_trace(go.Scatter(x=trend["dates"], y=trend[ch], name=ch.capitalize(),
            line=dict(color=col, width=2, dash=dashes_map[ch]), mode="lines"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=230,
        margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(orientation="h",y=-0.18,x=0,font=dict(color="#6b7280",size=11),bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=True,gridcolor="#1a1e27",tickfont=dict(color="#6b7280",size=10),nticks=7,showline=False),
        yaxis=dict(showgrid=True,gridcolor="#1a1e27",tickfont=dict(color="#6b7280",size=10),range=[30,100],showline=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    # Sentiment breakdown
    base = kpis["sentiment_score"]
    channels = ["Twitter / X","Instagram","YouTube","Reddit","Ticket Reviews"]
    scores = [min(99,int(base*m)) for m in [.95,1.08,.92,1.0,.82]]
    bar_c = ["#3d9cf0","#c8f135","#f59e0b","#ef4444","#a78bfa"]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=scores, y=channels, orientation="h", marker=dict(color=bar_c),
        text=[str(s) for s in scores], textposition="outside",
        textfont=dict(color="#e8eaf0",size=11)))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=190,
        margin=dict(l=0,r=40,t=20,b=0), title=dict(text="Sentiment by channel",
        font=dict(family="Syne",size=13,color="#e8eaf0"), x=0),
        xaxis=dict(range=[0,115],showgrid=False,showticklabels=False),
        yaxis=dict(tickfont=dict(color="#6b7280",size=11)), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

with col2:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:10px">Fan Risk Engine · per fixture</div>', unsafe_allow_html=True)

    for fr in risk["fixture_risks"]:
        risk_c = "#ef4444" if fr["risk_level"]=="HIGH" else "#f59e0b" if fr["risk_level"]=="MED" else "#22c55e"
        rival_tag = ' <span style="font-size:9px;color:#3d9cf0;border:1px solid #3d9cf0;padding:1px 5px;border-radius:4px">DERBY</span>' if fr["is_rival"] else ""
        home_tag = "🏠" if fr["home"] else "✈"
        st.markdown(f"""
        <div style="background:#13161d;border:1px solid #1f2937;border-left:3px solid {risk_c};border-radius:8px;padding:12px 14px;margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <div style="font-size:12px;color:#e8eaf0;font-weight:500">{home_tag} vs {fr['opponent']}{rival_tag}</div>
                <div style="text-align:right">
                    <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:700;color:{risk_c};line-height:1">{fr['risk_score']}</div>
                    <div style="font-size:9px;color:#374151">/ 100 risk</div>
                </div>
            </div>
            <div style="font-size:10px;color:#6b7280;margin-bottom:6px">{fr['date']} · {fr['days_away']}d away · Capacity {fr['att_pct']}%</div>
            <div style="background:#0a0c10;border-radius:4px;height:5px;overflow:hidden">
                <div style="width:{fr['risk_score']}%;height:100%;background:{risk_c};border-radius:4px"></div>
            </div>
        </div>""", unsafe_allow_html=True)

    # Form + Sentiment split
    st.markdown(f"""
    <div style="background:#13161d;border:1px solid #1f2937;border-radius:10px;padding:14px 16px;margin-top:4px">
        <div style="font-size:10px;color:#6b7280;margin-bottom:8px;text-transform:uppercase;letter-spacing:.08em">Last 5 matches</div>
        <div style="margin-bottom:12px">{''.join(form_pill_comp(r, c) for r, c in zip(form, form_comp))}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;text-align:center">
            <div><div style="font-size:10px;color:#22c55e">POS</div><div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#22c55e">{sent['positive_pct']}%</div></div>
            <div><div style="font-size:10px;color:#6b7280">NEU</div><div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#6b7280">{sent['neutral_pct']}%</div></div>
            <div><div style="font-size:10px;color:#ef4444">NEG</div><div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#ef4444">{sent['negative_pct']}%</div></div>
        </div>
        <div style="font-size:10px;color:#374151;margin-top:8px">Based on {sent['post_count']} posts analysed</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Row 2: Signals + Content + Tickets ───────────────────────────────────────
s1, s2, s3 = st.columns([1.3, 1, 1])

with s1:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:10px">Fan intelligence signals</div>', unsafe_allow_html=True)
    priority_border = {"HIGH":"#ef4444","MED":"#f59e0b","OPT":"#3d9cf0","LOW":"#22c55e"}
    priority_bg     = {"HIGH":"#1f0a0a","MED":"#1c1500","OPT":"#0a1020","LOW":"#0a1f0a"}
    for sig in signals:
        bc = priority_border.get(sig["priority"],"#2a2f3d")
        bg = priority_bg.get(sig["priority"],"#13161d")

        # Claude AI recommendation for HIGH signals
        ai_block = ""
        if sig["priority"] == "HIGH":
            rec = get_claude_recommendation(selected, sig["title"], sig["desc"])
            if rec:
                lines = rec.strip().split("\n")
                formatted = "".join(
                    f'<div style="margin-bottom:3px"><span style="color:#c8f135;font-size:9px">{l.split(":")[0]}:</span>'
                    f'<span style="color:#9ca3af;font-size:9px"> {":".join(l.split(":")[1:]).strip()}</span></div>'
                    for l in lines if ":" in l
                )
                ai_block = f"""
                <div style="background:#0a0c10;border:1px solid #1a2a10;border-radius:6px;padding:8px 10px;margin-top:8px">
                    <div style="font-size:9px;color:#c8f135;margin-bottom:5px;letter-spacing:.05em">✦ CLAUDE AI RECOMMENDATION</div>
                    {formatted}
                </div>"""

        st.markdown(f"""
        <div style="background:{bg};border:1px solid #1f2937;border-left:3px solid {bc};border-radius:8px;padding:12px 14px;margin-bottom:10px">
            <div style="font-size:12px;color:#e8eaf0;font-weight:500;margin-bottom:4px">
                {risk_badge(sig['priority'])}{sig['title']}
            </div>
            <div style="font-size:11px;color:#6b7280;line-height:1.5;margin-bottom:6px">{sig['desc']}</div>
            <div style="font-size:10px;color:#3d9cf0">→ {sig.get('action','Review data')}</div>
            {ai_block}
        </div>""", unsafe_allow_html=True)

with s2:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:10px">Top content · YouTube</div>', unsafe_allow_html=True)
    for v in content["top_videos"][:4]:
        views = v["views"]
        vfmt = f"{views/1_000_000:.1f}M" if views>=1_000_000 else f"{views//1000}K" if views>=1000 else str(views)
        eng = round(v["likes"]/views*100,1) if views>0 else 0
        title = v["title"][:48]+("..." if len(v["title"])>48 else "")
        url_part = f'<a href="{v["url"]}" target="_blank" style="color:#3d9cf0;font-size:9px">▶ Watch</a>' if v.get("url") else ""
        st.markdown(f"""
        <div style="background:#13161d;border:1px solid #1f2937;border-radius:8px;padding:10px 12px;margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div style="flex:1;min-width:0">
                    <div style="font-size:11px;color:#e8eaf0;margin-bottom:3px;line-height:1.4">{title}</div>
                    <div style="font-size:10px;color:#6b7280">{v['published']} {url_part}</div>
                </div>
                <div style="text-align:right;margin-left:10px;flex-shrink:0">
                    <div style="font-family:Syne,sans-serif;font-size:15px;font-weight:700;color:#c8f135">{vfmt}</div>
                    <div style="font-size:9px;color:#6b7280">{eng}% eng</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

with s3:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:10px">Ticket demand · Next fixtures</div>', unsafe_allow_html=True)
    for f in tickets["fixtures"]:
        pct = f["att_pct"]
        bar_c = "#c8f135" if pct>=80 else "#3d9cf0" if pct>=60 else "#ef4444"
        vel_c = "#22c55e" if "fast" in f["velocity"].lower() else "#3d9cf0" if "Rising" in f["velocity"] else "#6b7280"
        home_icon = "🏠" if f["home"] else "✈"
        derby_tag = ' <span style="font-size:9px;color:#f59e0b">DERBY</span>' if f["is_rival"] else ""
        st.markdown(f"""
        <div style="background:#13161d;border:1px solid #1f2937;border-radius:8px;padding:12px 14px;margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                <div style="font-size:12px;color:#e8eaf0">{home_icon} vs {f['opponent']}{derby_tag}</div>
                <div style="font-family:Syne,sans-serif;font-size:14px;font-weight:600;color:{bar_c}">{pct}%</div>
            </div>
            <div style="background:#0a0c10;border-radius:3px;height:4px;margin-bottom:6px;overflow:hidden">
                <div style="width:{pct}%;height:100%;background:{bar_c};border-radius:3px"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:10px">
                <span style="color:#6b7280">{f['date']}</span>
                <span style="color:{vel_c}">{f['velocity']}</span>
            </div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

<<<<<<< HEAD
=======
# ── Commercial Impact Summary ─────────────────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:8px 0 14px'>", unsafe_allow_html=True)
st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:12px">Commercial Impact Summary · signal cascade</div>', unsafe_allow_html=True)

# Build the chain dynamically from loaded data
_sent_delta   = kpis["sentiment_score"] - 65
_sent_dir     = "up" if _sent_delta >= 0 else "down"
_sent_node_c  = "#22c55e" if _sent_delta >= 0 else "#ef4444"
_sent_node_bg = "#0a1f0a" if _sent_delta >= 0 else "#1f0a0a"
_sent_txt     = f"Sentiment {_sent_dir} {'+' if _sent_delta>=0 else ''}{_sent_delta} vs league avg"
_sent_sub     = f"Score: {kpis['sentiment_score']}/100"

_dem_pct   = round(kpis["demand_index"] * 100)
_dem_label = "Strong" if _dem_pct >= 75 else "Average" if _dem_pct >= 58 else "Below target"
_dem_c     = "#22c55e" if _dem_pct >= 75 else "#f59e0b" if _dem_pct >= 58 else "#ef4444"
_dem_bg    = "#0a1f0a" if _dem_pct >= 75 else "#1c1500" if _dem_pct >= 58 else "#1f0a0a"
_dem_txt   = f"Ticket demand {_dem_label.lower()}"
_dem_sub   = f"Avg fill: {_dem_pct}%"

_sp_fixtures = sponsor_exposure.get("fixtures", [])
_top_sp    = max(_sp_fixtures, key=lambda x: x["sponsor_index"]) if _sp_fixtures else None
_sp_idx    = _top_sp["sponsor_index"] if _top_sp else 0
_sp_label  = "Elevated" if _sp_idx >= 70 else "Moderate" if _sp_idx >= 50 else "Low"
_sp_c      = "#c8f135" if _sp_idx >= 70 else "#3d9cf0" if _sp_idx >= 50 else "#6b7280"
_sp_bg     = "#0f1a08" if _sp_idx >= 70 else "#0a1020" if _sp_idx >= 50 else "#13161d"
_sp_txt    = f"Sponsor exposure {_sp_label.lower()}"
_sp_sub    = f"Peak index: {_sp_idx}" + (" · DERBY" if _top_sp and _top_sp.get("is_rival") else "")

# Best action: first HIGH signal, else first signal, else fallback
_best_signal  = next((s for s in signals if s["priority"]=="HIGH"), signals[0] if signals else None)
_action_title = _best_signal["action"] if _best_signal else "Review fan intelligence data"
_action_why   = _best_signal["title"] if _best_signal else ""
_action_c     = "#c8f135"
_action_bg    = "#0f1a08"

# Build narrative sentence
_narrative = (
    f"{_sent_txt} · {_dem_txt} at {_dem_pct}% avg capacity · "
    f"Sponsor exposure {_sp_label.lower()} (peak index {_sp_idx}) · "
    f"Action: {_action_title}"
)

st.markdown(f"""
<div style="background:#13161d;border:1px solid #1f2937;border-radius:10px;padding:16px 20px">
    <div style="display:flex;align-items:stretch;gap:0;flex-wrap:wrap;margin-bottom:14px">
        <div style="background:{_sent_node_bg};border:1px solid {_sent_node_c}40;border-radius:8px 0 0 8px;padding:12px 16px;flex:1;min-width:120px">
            <div style="font-size:8px;color:{_sent_node_c};letter-spacing:.08em;margin-bottom:5px;text-transform:uppercase">Sentiment Score</div>
            <div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:{_sent_node_c}">{_sent_txt.split(" at ")[0]}</div>
            <div style="font-size:10px;color:#4b5563;margin-top:2px">{_sent_sub}</div>
        </div>
        <div style="display:flex;align-items:center;padding:0 6px;color:#374151;font-size:20px;flex-shrink:0">›</div>
        <div style="background:{_dem_bg};border:1px solid {_dem_c}40;border-radius:0;padding:12px 16px;flex:1;min-width:120px">
            <div style="font-size:8px;color:{_dem_c};letter-spacing:.08em;margin-bottom:5px;text-transform:uppercase">Ticket Demand</div>
            <div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:{_dem_c}">{_dem_label}</div>
            <div style="font-size:10px;color:#4b5563;margin-top:2px">{_dem_sub}</div>
        </div>
        <div style="display:flex;align-items:center;padding:0 6px;color:#374151;font-size:20px;flex-shrink:0">›</div>
        <div style="background:{_sp_bg};border:1px solid {_sp_c}40;border-radius:0;padding:12px 16px;flex:1;min-width:120px">
            <div style="font-size:8px;color:{_sp_c};letter-spacing:.08em;margin-bottom:5px;text-transform:uppercase">Sponsor Exposure</div>
            <div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:{_sp_c}">{_sp_label}</div>
            <div style="font-size:10px;color:#4b5563;margin-top:2px">{_sp_sub}</div>
        </div>
        <div style="display:flex;align-items:center;padding:0 6px;color:#374151;font-size:20px;flex-shrink:0">›</div>
        <div style="background:{_action_bg};border:1px solid {_action_c};border-radius:0 8px 8px 0;padding:12px 16px;flex:1.4;min-width:160px">
            <div style="font-size:8px;color:{_action_c};letter-spacing:.08em;margin-bottom:5px;text-transform:uppercase">Recommended Action</div>
            <div style="font-size:12px;font-weight:500;color:#e8eaf0;line-height:1.4">{_action_title}</div>
            <div style="font-size:10px;color:#4b5563;margin-top:3px;line-height:1.4">{_action_why[:60]}{'...' if len(_action_why)>60 else ''}</div>
        </div>
    </div>
    <div style="font-size:10px;color:#374151;font-style:italic;border-top:1px solid #1a1e27;padding-top:10px">
        ↳ {_narrative}
    </div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

>>>>>>> origin/claude/suspicious-leakey
# ── Fan Cohort Breakdown ──────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:8px 0 14px'>", unsafe_allow_html=True)
st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:12px">Fan cohort breakdown · at-risk segments</div>', unsafe_allow_html=True)

cohort_cols = st.columns(len(cohorts))
for i, cohort in enumerate(cohorts):
    r = cohort["risk_score"]
    risk_c = "#ef4444" if r >= 65 else "#f59e0b" if r >= 40 else "#22c55e"
    risk_bg = "#1f0a0a" if r >= 65 else "#1c1500" if r >= 40 else "#0a1f0a"
    risk_label = "HIGH RISK" if r >= 65 else "MED RISK" if r >= 40 else "LOW RISK"
    eng = cohort["engagement"]
    with cohort_cols[i]:
        st.markdown(f"""
        <div style="background:#13161d;border:1px solid #1f2937;border-top:3px solid {risk_c};border-radius:8px;padding:14px 12px;height:100%">
            <div style="font-size:11px;color:#e8eaf0;font-weight:500;margin-bottom:8px">{cohort['name']}</div>
            <div style="font-family:Syne,sans-serif;font-size:26px;font-weight:800;color:{risk_c};line-height:1">{r}</div>
            <div style="font-size:9px;color:{risk_c};margin-bottom:2px;letter-spacing:.05em">{risk_label}</div>
            <div style="font-size:9px;color:#374151;margin-bottom:8px">risk score · 0 – 100</div>
            <div style="background:#0a0c10;border-radius:3px;height:4px;margin-bottom:8px;overflow:hidden">
                <div style="width:{r}%;height:100%;background:{risk_c};border-radius:3px"></div>
            </div>
            <div style="font-size:9px;color:#6b7280;margin-bottom:4px">{cohort['size_pct']}% of fanbase</div>
            <div style="font-size:9px;color:#4b5563;margin-bottom:8px">Engagement: {eng}%</div>
            <div style="font-size:9px;color:#3d9cf0;line-height:1.4">→ {cohort['action']}</div>
        </div>""", unsafe_allow_html=True)

# ── League context strip ──────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:16px 0 16px'>", unsafe_allow_html=True)
st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:10px">WSL standings context</div>', unsafe_allow_html=True)

league_clubs = {k: v for k, v in WSL_LEAGUE_CONTEXT.items()}
lc = st.columns(len(league_clubs))
for i, (club, data) in enumerate(league_clubs.items()):
    is_selected = club == selected
    bg = "#1a2010" if is_selected else "#13161d"
    border = "#c8f135" if is_selected else "#1f2937"
    form_str = " ".join(data["last_5_form"])
    with lc[i]:
        st.markdown(f"""
        <div style="background:{bg};border:1px solid {border};border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:10px;color:{'#c8f135' if is_selected else '#9ca3af'};font-weight:500;margin-bottom:4px">{club}</div>
            <div style="font-family:Syne,sans-serif;font-size:22px;font-weight:800;color:{'#c8f135' if is_selected else '#e8eaf0'}">#{data['position']}</div>
            <div style="font-size:11px;color:#6b7280">{data['pts']} pts</div>
            <div style="font-size:10px;color:#4b5563;margin-top:4px">{form_str}</div>
        </div>""", unsafe_allow_html=True)

# ── Feature 1: Attendance Prediction Engine ───────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:16px 0 16px'>", unsafe_allow_html=True)
st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
    <span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0">Attendance Prediction Engine · per fixture</span>
    <span style="background:#1c1500;color:#f59e0b;border:1px solid #92400e;font-size:9px;padding:2px 8px;border-radius:10px">◯ Simulated model</span>
</div>""", unsafe_allow_html=True)

if att_preds:
    att_cols = st.columns(len(att_preds))
    for i, ap in enumerate(att_preds):
        pred    = ap["predicted_pct"]
        low     = ap["confidence_low"]
        high    = ap["confidence_high"]
        at_risk = ap["at_risk"]
        drv     = ap["drivers"]
        bar_c      = "#ef4444" if at_risk else "#c8f135" if pred >= 85 else "#3d9cf0"
        border_c   = "#ef4444" if at_risk else "#1f2937"
        home_icon  = "🏠" if ap["home"] else "✈"
        rival_html = '<span style="font-size:9px;color:#3d9cf0;border:1px solid #3d9cf0;padding:1px 5px;border-radius:4px;margin-left:4px">DERBY</span>' if ap["is_rival"] else ""
        risk_html  = '<div style="background:#1f0a0a;border:1px solid #ef4444;color:#ef4444;font-size:9px;padding:3px 8px;border-radius:6px;text-align:center;margin-bottom:8px">AT RISK — BELOW 70%</div>' if at_risk else ""
        sent_sign  = "+" if drv["sentiment_adj"] >= 0 else ""
        card_html = (
            f'<div style="background:#13161d;border:1px solid {border_c};border-top:3px solid {bar_c};border-radius:8px;padding:14px">'
            + risk_html
            + f'<div style="font-size:11px;color:#e8eaf0;margin-bottom:4px">{home_icon} vs {ap["opponent"]}{rival_html}</div>'
            + f'<div style="font-size:10px;color:#4b5563;margin-bottom:10px">{ap["date"]} · {ap["days_away"]}d away</div>'
            + f'<div style="font-family:Syne,sans-serif;font-size:32px;font-weight:800;color:{bar_c};line-height:1">{pred}%</div>'
            + '<div style="font-size:10px;color:#6b7280;margin-bottom:8px">predicted capacity fill</div>'
            + f'<div style="font-size:10px;color:#4b5563;margin-bottom:4px">Confidence range: {low}% &ndash; {high}%</div>'
            + f'<div style="background:#0a0c10;border-radius:4px;height:5px;overflow:hidden;margin-bottom:10px">'
            + f'<div style="width:{pred}%;height:100%;background:{bar_c};border-radius:4px"></div>'
            + '</div>'
            + f'<div style="font-size:9px;color:#4b5563;margin-bottom:2px">Hist avg: {drv["historical"]}% | Sentiment: {sent_sign}{drv["sentiment_adj"]}%</div>'
            + f'<div style="font-size:9px;color:#374151">Derby bonus: +{drv["derby_bonus"]}% | Form adj: {drv["form_penalty"]}%</div>'
            + '</div>'
        )
        with att_cols[i]:
            st.markdown(card_html, unsafe_allow_html=True)
else:
    st.markdown('<div style="color:#4b5563;font-size:11px">No fixture data available.</div>', unsafe_allow_html=True)

# ── Feature 2: Fan Churn Risk Score ───────────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:20px 0 16px'>", unsafe_allow_html=True)
st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
    <span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0">Fan Churn Risk Score · per cohort</span>
    <span style="background:#1c1500;color:#f59e0b;border:1px solid #92400e;font-size:9px;padding:2px 8px;border-radius:10px">◯ Simulated model</span>
</div>""", unsafe_allow_html=True)

churn_cols = st.columns(len(churn_risks))
for i, cr in enumerate(churn_risks):
    churn = cr["churn_pct"]
    rl    = cr["risk_level"]
    rc    = "#ef4444" if rl=="HIGH" else "#f59e0b" if rl=="MED" else "#22c55e"
    rb    = "#1f0a0a" if rl=="HIGH" else "#1c1500" if rl=="MED" else "#0a1f0a"
    with churn_cols[i]:
        st.markdown(f"""
        <div style="background:#13161d;border:1px solid #1f2937;border-top:3px solid {rc};border-radius:8px;padding:14px 12px;height:100%">
            <div style="font-size:11px;color:#e8eaf0;font-weight:500;margin-bottom:8px">{cr['name']}</div>
            <div style="font-family:Syne,sans-serif;font-size:28px;font-weight:800;color:{rc};line-height:1">{churn}%</div>
            <div style="font-size:9px;color:{rc};margin-bottom:2px;letter-spacing:.05em">CHURN RISK</div>
            <div style="font-size:9px;color:#374151;margin-bottom:8px">% of cohort at risk of lapsing</div>
            <div style="background:#0a0c10;border-radius:3px;height:4px;margin-bottom:10px;overflow:hidden">
                <div style="width:{churn}%;height:100%;background:{rc};border-radius:3px"></div>
            </div>
            <div style="background:{rb};border:1px solid {rc}22;border-radius:5px;padding:6px 8px">
                <div style="font-size:8px;color:{rc};letter-spacing:.05em;margin-bottom:3px">RETENTION ACTION</div>
                <div style="font-size:9px;color:#9ca3af;line-height:1.5">→ {cr['retention_action']}</div>
            </div>
        </div>""", unsafe_allow_html=True)

# ── Feature 3: Player Sentiment Influence ─────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:20px 0 16px'>", unsafe_allow_html=True)
st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
    <span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0">Player Sentiment Influence · ranked by marketing value</span>
    <span style="background:#1c1500;color:#f59e0b;border:1px solid #92400e;font-size:9px;padding:2px 8px;border-radius:10px">◯ Simulated data</span>
</div>""", unsafe_allow_html=True)

if player_influence:
    top_player = player_influence[0]
    p1c, p2c = st.columns([1.1, 2])

    with p1c:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0f1a08,#13161d);border:1px solid #c8f135;border-radius:10px;padding:18px 16px;height:100%">
            <div style="font-size:9px;color:#c8f135;letter-spacing:.08em;margin-bottom:10px">✦ TOP SENTIMENT PLAYER</div>
            <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:#c8f135;margin-bottom:2px">{top_player['name']}</div>
            <div style="font-size:10px;color:#6b7280;margin-bottom:14px">{top_player['position']} · {top_player['club']}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
                <div style="background:#0a0c10;border-radius:6px;padding:8px;text-align:center">
                    <div style="font-size:9px;color:#6b7280;margin-bottom:2px">Sentiment lift</div>
                    <div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#c8f135">+{top_player['sentiment_lift']}</div>
                    <div style="font-size:8px;color:#374151">pts above club avg</div>
                </div>
                <div style="background:#0a0c10;border-radius:6px;padding:8px;text-align:center">
                    <div style="font-size:9px;color:#6b7280;margin-bottom:2px">Engagement ×</div>
                    <div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#3d9cf0">{top_player['engagement_mult']}x</div>
                    <div style="font-size:8px;color:#374151">vs club baseline</div>
                </div>
                <div style="background:#0a0c10;border-radius:6px;padding:8px;text-align:center">
                    <div style="font-size:9px;color:#6b7280;margin-bottom:2px">Merch index</div>
                    <div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#a78bfa">{top_player['merch_index']}</div>
                    <div style="font-size:8px;color:#374151">0 – 100 demand score</div>
                </div>
                <div style="background:#0a0c10;border-radius:6px;padding:8px;text-align:center">
                    <div style="font-size:9px;color:#6b7280;margin-bottom:2px">Mktg value</div>
                    <div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#f59e0b">{top_player['marketing_value']}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    with p2c:
        header_html = """
        <div style="display:grid;grid-template-columns:28px 1fr 80px 80px 90px 80px;gap:6px;padding:0 14px;margin-bottom:6px">
            <div style="font-size:9px;color:#4b5563">#</div>
            <div style="font-size:9px;color:#4b5563">PLAYER</div>
            <div style="font-size:9px;color:#4b5563;text-align:center">SENT LIFT<br><span style="font-size:8px;color:#374151">pts vs avg</span></div>
            <div style="font-size:9px;color:#4b5563;text-align:center">ENG ×<br><span style="font-size:8px;color:#374151">vs baseline</span></div>
            <div style="font-size:9px;color:#4b5563;text-align:center">MERCH IDX<br><span style="font-size:8px;color:#374151">0 – 100</span></div>
            <div style="font-size:9px;color:#4b5563;text-align:center">MKTG VAL</div>
        </div>"""
        st.markdown(header_html, unsafe_allow_html=True)
        for rank, p in enumerate(player_influence, 1):
            is_top = rank == 1
            bg = "#0f1a08" if is_top else "#13161d"
            border = "#c8f135" if is_top else "#1f2937"
            name_color = "#c8f135" if is_top else "#e8eaf0"
            merch_bar_w = p['merch_index']
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};border-radius:7px;padding:10px 14px;margin-bottom:6px;
                        display:grid;grid-template-columns:28px 1fr 80px 80px 90px 80px;gap:6px;align-items:center">
                <div style="font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:#374151">#{rank}</div>
                <div>
                    <div style="font-size:11px;color:{name_color};font-weight:500">{p['name']}</div>
                    <div style="font-size:9px;color:#4b5563">{p['position']} · {p['club']}</div>
                </div>
                <div style="text-align:center;font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#c8f135">+{p['sentiment_lift']}</div>
                <div style="text-align:center;font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#3d9cf0">{p['engagement_mult']}x</div>
                <div style="text-align:center">
                    <div style="background:#0a0c10;border-radius:3px;height:4px;margin-bottom:3px;overflow:hidden">
                        <div style="width:{merch_bar_w}%;height:100%;background:#a78bfa;border-radius:3px"></div>
                    </div>
                    <div style="font-size:10px;color:#a78bfa">{p['merch_index']}</div>
                </div>
                <div style="text-align:center;font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:#f59e0b">{p['marketing_value']}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.markdown('<div style="color:#4b5563;font-size:11px">No player data available.</div>', unsafe_allow_html=True)

# ── Feature 4: Sponsor Exposure Score ─────────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:20px 0 16px'>", unsafe_allow_html=True)
st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
    <span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0">Sponsor Exposure Score · per fixture</span>
    <span style="background:#1c1500;color:#f59e0b;border:1px solid #92400e;font-size:9px;padding:2px 8px;border-radius:10px">◯ Simulated model</span>
</div>""", unsafe_allow_html=True)

sp_fixtures = sponsor_exposure["fixtures"]
league_avg  = sponsor_exposure["league_avg"]

if sp_fixtures:
    sp_cols = st.columns(len(sp_fixtures))
    for i, sf in enumerate(sp_fixtures):
        idx  = sf["sponsor_index"]
        vs_b = sf["vs_benchmark"]
        is_p = sf["is_premium"]
        idx_c     = "#c8f135" if is_p else "#3d9cf0" if idx >= 55 else "#6b7280"
        vs_c      = "#22c55e" if vs_b >= 0 else "#ef4444"
        border_c  = "#c8f135" if is_p else "#1f2937"
        home_icon = "🏠" if sf["home"] else "✈"
        rival_html   = '<span style="font-size:9px;color:#f59e0b;margin-left:4px">DERBY</span>' if sf["is_rival"] else ""
        premium_html = '<div style="background:#0f1a08;border:1px solid #c8f135;color:#c8f135;font-size:9px;padding:3px 8px;border-radius:6px;text-align:center;margin-bottom:10px">PREMIUM SLOT</div>' if is_p else ""
        vs_sign = "+" if vs_b >= 0 else ""
        sp_card = (
            f'<div style="background:#13161d;border:1px solid {border_c};border-radius:8px;padding:14px">'
            + premium_html
            + f'<div style="font-size:11px;color:#e8eaf0;margin-bottom:4px">{home_icon} vs {sf["opponent"]}{rival_html}</div>'
            + f'<div style="font-size:10px;color:#4b5563;margin-bottom:10px">{sf["date"]}</div>'
            + f'<div style="font-family:Syne,sans-serif;font-size:32px;font-weight:800;color:{idx_c};line-height:1">{idx}</div>'
            + '<div style="font-size:10px;color:#6b7280;margin-bottom:8px">sponsor value index / 100</div>'
            + f'<div style="background:#0a0c10;border-radius:4px;height:6px;overflow:hidden;margin-bottom:10px">'
            + f'<div style="width:{idx}%;height:100%;background:{idx_c};border-radius:4px"></div>'
            + '</div>'
            + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">'
            + f'<div style="background:#0a0c10;border-radius:5px;padding:7px;text-align:center">'
            + f'<div style="font-size:9px;color:#4b5563;margin-bottom:2px">vs WSL avg ({league_avg})</div>'
            + f'<div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:{vs_c}">{vs_sign}{vs_b}</div>'
            + '</div>'
            + '<div style="background:#0a0c10;border-radius:5px;padding:7px;text-align:center">'
            + '<div style="font-size:9px;color:#4b5563;margin-bottom:2px">Broadcast reach</div>'
            + f'<div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:#a78bfa">{sf["broadcast_reach"]}</div>'
            + '</div>'
            + '</div>'
            + '</div>'
        )
        with sp_cols[i]:
            st.markdown(sp_card, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-size:10px;color:#374151;text-align:center;padding:20px 0 8px;border-top:1px solid #1f2937;margin-top:16px">
    FanIntel WSL · May 2025 ·
    Live: YouTube + Reddit · Simulated: X, TikTok, Ticketing · Not production data
</div>""", unsafe_allow_html=True)
