import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from data import get_full_club_data, WSL_CLUBS

st.set_page_config(
    page_title="WSL Fan Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"], [class*="stMarkdown"] { font-family: 'DM Mono', monospace; }
[data-testid="stAppViewContainer"] { background-color: #0d0f14; }
[data-testid="stHeader"] { background-color: #0d0f14; }
section[data-testid="stSidebar"] { display: none; }
div[data-testid="stRadio"] > label { display: none; }
div[data-testid="stRadio"] > div { flex-direction: row; flex-wrap: wrap; gap: 8px; }
div[data-testid="stRadio"] > div > label {
    background: #1a1e27 !important;
    border: 1px solid #2a2f3d !important;
    border-radius: 6px !important;
    padding: 6px 16px !important;
    color: #6b7280 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    cursor: pointer !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: #c8f135 !important;
    border-color: #c8f135 !important;
    color: #0d0f14 !important;
    font-weight: 500 !important;
}
div[data-testid="stRadio"] > div > label > div { display: none !important; }
.dash-title { font-family: 'Syne', sans-serif; font-size: 26px; font-weight: 700; color: #c8f135; letter-spacing: -0.5px; }
.dash-sub { font-size: 12px; color: #6b7280; margin-top: 2px; }
.kpi-card { background: #1a1e27; border: 1px solid #2a2f3d; border-radius: 8px; padding: 16px 18px; }
.kpi-label { font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 32px; font-weight: 700; color: #e8eaf0; line-height: 1; }
.kpi-delta-up { font-size: 11px; color: #22c55e; margin-top: 6px; }
.kpi-delta-down { font-size: 11px; color: #ef4444; margin-top: 6px; }
.kpi-delta-flat { font-size: 11px; color: #6b7280; margin-top: 6px; }
.panel { background: #1a1e27; border: 1px solid #2a2f3d; border-radius: 8px; padding: 16px 18px; margin-bottom: 14px; }
.panel-title { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 600; color: #e8eaf0; margin-bottom: 14px; }
.signal-item { padding: 10px 12px; border-radius: 6px; margin-bottom: 8px; background: #13161d; }
.signal-high { border-left: 3px solid #c8f135; }
.signal-med  { border-left: 3px solid #3d9cf0; }
.signal-opt  { border-left: 3px solid #f59e0b; }
.signal-title { font-size: 12px; color: #e8eaf0; font-weight: 500; margin-bottom: 3px; }
.signal-desc  { font-size: 11px; color: #6b7280; line-height: 1.5; }
.badge { float: right; font-size: 9px; padding: 2px 6px; border-radius: 8px; background: #1a1e27; color: #6b7280; margin-left: 8px; border: 1px solid #2a2f3d; }
.video-item { background: #13161d; border: 1px solid #2a2f3d; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
.video-title { font-size: 12px; color: #e8eaf0; }
.video-meta  { font-size: 10px; color: #6b7280; margin-top: 2px; }
.video-views { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 600; color: #c8f135; }
.pill { display: inline-block; font-size: 9px; padding: 2px 8px; border-radius: 10px; margin-right: 4px; }
.pill-live { background: #052e16; color: #22c55e; border: 1px solid #166534; }
.pill-sim  { background: #431407; color: #f59e0b; border: 1px solid #92400e; }
.footer { font-size: 10px; color: #374151; text-align: center; padding: 20px 0 8px; border-top: 1px solid #1f2937; margin-top: 8px; }
div[data-testid="column"] > div { gap: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
c1, c2 = st.columns([5, 1])
with c1:
    st.markdown('<div class="dash-title">FanIntel <span style="color:#6b7280;font-weight:400">/ WSL Edition</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Women\'s Super League · 2024–25 Season · Fan Intelligence Prototype</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right;padding-top:12px"><span style="background:#13161d;border:1px solid #2a2f3d;color:#6b7280;font-size:11px;padding:5px 12px;border-radius:20px">🟢 Live</span></div>', unsafe_allow_html=True)

st.markdown("<hr style='border-color:#2a2f3d;margin:14px 0 10px'>", unsafe_allow_html=True)

# ── Club selector ─────────────────────────────────────────────────────────────
selected_club = st.radio("Club", list(WSL_CLUBS.keys()), horizontal=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner(f"Loading fan intelligence for {selected_club}..."):
    data = get_full_club_data(selected_club)

kpis     = data["kpis"]
sentiment= data["sentiment"]
content  = data["content"]
tickets  = data["tickets"]
trend    = data["trend"]
signals  = data["signals"]
sources  = data["data_sources"]

# ── Source pills ──────────────────────────────────────────────────────────────
def pill(label, live):
    cls = "pill-live" if live else "pill-sim"
    dot = "⬤" if live else "◯"
    return f'<span class="pill {cls}">{dot} {label}</span>'

st.markdown(
    '<span style="font-size:10px;color:#6b7280;margin-right:6px">Data sources:</span>'
    + pill("Reddit sentiment", sources["sentiment"]=="live")
    + pill("YouTube", sources["content"]=="live")
    + pill("Ticketing", False)
    + pill("X / TikTok", False),
    unsafe_allow_html=True
)
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ── KPI cards ─────────────────────────────────────────────────────────────────
def kpi(label, value, delta, direction):
    arrow = "▲" if direction=="up" else "▼" if direction=="down" else "—"
    cls   = f"kpi-delta-{direction}"
    return f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="{cls}">{arrow} {delta}</div>
    </div>"""

k1,k2,k3,k4 = st.columns(4)
with k1: st.markdown(kpi("Sentiment Score", kpis["sentiment_score"],
    f"{kpis['sentiment_score']-65:+d} vs league avg",
    "up" if kpis["sentiment_score"]>=65 else "down"), unsafe_allow_html=True)
with k2: st.markdown(kpi("Content Reach", kpis["content_reach"],
    "YouTube · last 8 videos", "flat"), unsafe_allow_html=True)
with k3: st.markdown(kpi("Ticket Demand Index", kpis["demand_index"],
    "Next 3 fixtures",
    "up" if kpis["demand_index"]>=0.75 else "flat"), unsafe_allow_html=True)
with k4: st.markdown(kpi("Risk Alerts", kpis["risk_alerts"],
    "Signals requiring action",
    "down" if kpis["risk_alerts"]>1 else "flat"), unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Main row ──────────────────────────────────────────────────────────────────
left, right = st.columns([2,1])

with left:
    # Sentiment trend
    st.markdown('<div class="panel"><div class="panel-title">Cross-channel sentiment · 14 days</div>', unsafe_allow_html=True)
    colors = {"twitter":"#3d9cf0","instagram":"#c8f135","youtube":"#f59e0b","reddit":"#ef4444"}
    dashes = {"twitter":"solid","instagram":"solid","youtube":"dash","reddit":"dot"}
    fig = go.Figure()
    for ch,col in colors.items():
        fig.add_trace(go.Scatter(x=trend["dates"], y=trend[ch], name=ch.capitalize(),
            line=dict(color=col, width=2, dash=dashes[ch]), mode="lines"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=220,
        margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(orientation="h",y=-0.18,x=0,font=dict(color="#6b7280",size=11),bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=True,gridcolor="#1f2937",tickfont=dict(color="#6b7280",size=10),nticks=7,showline=False),
        yaxis=dict(showgrid=True,gridcolor="#1f2937",tickfont=dict(color="#6b7280",size=10),range=[30,100],showline=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Sentiment bars
    st.markdown('<div class="panel"><div class="panel-title">Sentiment breakdown by channel</div>', unsafe_allow_html=True)
    base = kpis["sentiment_score"]
    channels = ["Twitter / X","Instagram","YouTube","Reddit","Ticket Reviews"]
    scores   = [int(base*.95), int(base*1.08), int(base*.92), sentiment["score"], int(base*.82)]
    scores   = [min(s,99) for s in scores]
    bar_colors = ["#3d9cf0","#c8f135","#f59e0b","#ef4444","#a78bfa"]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=scores, y=channels, orientation="h",
        marker=dict(color=bar_colors),
        text=[str(s) for s in scores], textposition="outside",
        textfont=dict(color="#e8eaf0",size=11)))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=200,
        margin=dict(l=0,r=40,t=0,b=0),
        xaxis=dict(range=[0,115],showgrid=False,showticklabels=False),
        yaxis=dict(tickfont=dict(color="#6b7280",size=11)), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    # Sentiment summary
    pos = sentiment["positive_pct"]
    neu = sentiment["neutral_pct"]
    neg = sentiment["negative_pct"]
    st.markdown(f"""<div class="panel">
        <div class="panel-title">Sentiment summary</div>
        <div style="display:flex;gap:8px;margin-bottom:12px">
            <div style="flex:1;background:#13161d;border-radius:6px;padding:10px;text-align:center">
                <div style="font-size:10px;color:#22c55e;margin-bottom:3px">POSITIVE</div>
                <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#22c55e">{pos}%</div>
            </div>
            <div style="flex:1;background:#13161d;border-radius:6px;padding:10px;text-align:center">
                <div style="font-size:10px;color:#6b7280;margin-bottom:3px">NEUTRAL</div>
                <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#6b7280">{neu}%</div>
            </div>
            <div style="flex:1;background:#13161d;border-radius:6px;padding:10px;text-align:center">
                <div style="font-size:10px;color:#ef4444;margin-bottom:3px">NEGATIVE</div>
                <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#ef4444">{neg}%</div>
            </div>
        </div>
        <div style="font-size:10px;color:#6b7280">Based on {sentiment['post_count']} posts · Reddit + simulated channels</div>
    </div>""", unsafe_allow_html=True)

    # Fan signals
    st.markdown('<div class="panel"><div class="panel-title">Fan intelligence signals</div>', unsafe_allow_html=True)
    priority_class = {"HIGH":"signal-high","MED":"signal-med","OPT":"signal-opt"}
    for sig in signals:
        cls = priority_class.get(sig["priority"],"signal-opt")
        st.markdown(f"""<div class="signal-item {cls}">
            <div class="signal-title"><span class="badge">{sig['priority']}</span>{sig['title']}</div>
            <div class="signal-desc">{sig['desc']}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Bottom row ────────────────────────────────────────────────────────────────
b1, b2 = st.columns([1,1])

with b1:
    st.markdown('<div class="panel"><div class="panel-title">Top content · YouTube</div>', unsafe_allow_html=True)
    for v in content["top_videos"][:4]:
        views = v["views"]
        if views >= 1_000_000:
            vfmt = f"{views/1_000_000:.1f}M"
        elif views >= 1000:
            vfmt = f"{views//1000}K"
        else:
            vfmt = str(views)
        title = v["title"][:50] + ("..." if len(v["title"])>50 else "")
        st.markdown(f"""<div class="video-item">
            <div>
                <div class="video-title">{title}</div>
                <div class="video-meta">{v['published']}</div>
            </div>
            <div class="video-views">{vfmt}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with b2:
    st.markdown('<div class="panel"><div class="panel-title">Ticket demand · Next 3 fixtures</div>', unsafe_allow_html=True)
    fix = tickets["fixtures"]
    if fix:
        bar_c = ["#c8f135" if f["att_pct"]>=80 else "#3d9cf0" if f["att_pct"]>=60 else "#ef4444" for f in fix]
        labels = [f"{'🏠' if f['home'] else '✈'} {f['opponent']}" for f in fix]
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=[f["att_pct"] for f in fix], y=labels, orientation="h",
            marker=dict(color=bar_c),
            text=[f"{f['att_pct']}%" for f in fix], textposition="outside",
            textfont=dict(color="#e8eaf0",size=11)))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=160,
            margin=dict(l=0,r=50,t=0,b=0),
            xaxis=dict(range=[0,115],showgrid=False,showticklabels=False),
            yaxis=dict(tickfont=dict(color="#6b7280",size=11)), showlegend=False)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        for f in fix:
            vel_color = "#22c55e" if "fast" in f["velocity"].lower() else "#3d9cf0" if "Rising" in f["velocity"] else "#6b7280"
            icon = "🏠" if f["home"] else "✈"
            st.markdown(f"""<div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:4px">
                <span>{icon} {f['opponent']} · {f['date']}</span>
                <span style="color:{vel_color}">{f['velocity']}</span>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""<div class="footer">
    FanIntel WSL · Prototype for Two Circles pitch · Live: YouTube + Reddit · Simulated: X, TikTok, Ticketing
</div>""", unsafe_allow_html=True)
