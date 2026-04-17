import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
import sys

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

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
}

.main { background-color: #0d0f14; }
[data-testid="stAppViewContainer"] { background-color: #0d0f14; }
[data-testid="stHeader"] { background-color: #0d0f14; }

.dash-title {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: #c8f135;
    letter-spacing: -0.5px;
    margin: 0;
}
.dash-sub {
    font-size: 12px;
    color: #6b7280;
    margin-top: 2px;
}
.live-badge {
    display: inline-block;
    background: #13161d;
    border: 1px solid #2a2f3d;
    color: #6b7280;
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 20px;
}

.kpi-card {
    background: #1a1e27;
    border: 1px solid #2a2f3d;
    border-radius: 8px;
    padding: 16px;
    position: relative;
    overflow: hidden;
}
.kpi-label {
    font-size: 10px;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'Syne', sans-serif;
    font-size: 30px;
    font-weight: 700;
    color: #e8eaf0;
    line-height: 1;
}
.kpi-delta-up { font-size: 11px; color: #22c55e; margin-top: 5px; }
.kpi-delta-down { font-size: 11px; color: #ef4444; margin-top: 5px; }
.kpi-delta-flat { font-size: 11px; color: #6b7280; margin-top: 5px; }

.panel {
    background: #1a1e27;
    border: 1px solid #2a2f3d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}
.panel-title {
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #e8eaf0;
    margin-bottom: 14px;
}

.signal-item {
    padding: 10px 12px;
    border-radius: 6px;
    margin-bottom: 8px;
    background: #13161d;
}
.signal-high { border-left: 3px solid #c8f135; }
.signal-med  { border-left: 3px solid #3d9cf0; }
.signal-opt  { border-left: 3px solid #f59e0b; }
.signal-title { font-size: 12px; color: #e8eaf0; font-weight: 500; margin-bottom: 3px; }
.signal-desc  { font-size: 11px; color: #6b7280; }
.signal-badge {
    float: right;
    font-size: 9px;
    padding: 2px 6px;
    border-radius: 8px;
    background: #1a1e27;
    color: #6b7280;
    margin-left: 8px;
}

.video-item {
    background: #13161d;
    border: 1px solid #2a2f3d;
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.video-title { font-size: 12px; color: #e8eaf0; }
.video-meta  { font-size: 10px; color: #6b7280; margin-top: 2px; }
.video-views { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 600; color: #c8f135; }

.data-pill {
    display: inline-block;
    font-size: 9px;
    padding: 2px 7px;
    border-radius: 10px;
    margin-right: 4px;
}
.pill-live { background: #052e16; color: #22c55e; border: 1px solid #166534; }
.pill-sim  { background: #431407; color: #f59e0b; border: 1px solid #92400e; }

.footnote {
    font-size: 10px;
    color: #4b5563;
    text-align: center;
    padding: 20px 0 8px;
    border-top: 1px solid #1f2937;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
col_logo, col_badge = st.columns([6, 1])
with col_logo:
    st.markdown('<div class="dash-title">FanIntel <span style="color:#6b7280;font-weight:400">/ WSL Edition</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Women\'s Super League · 2024–25 Season · Fan Intelligence Prototype</div>', unsafe_allow_html=True)
with col_badge:
    st.markdown('<div class="live-badge">🟢 Live</div>', unsafe_allow_html=True)

st.markdown("<hr style='border-color:#2a2f3d;margin:16px 0'>", unsafe_allow_html=True)

# ── Club selector ────────────────────────────────────────────────────────────
clubs = list(WSL_CLUBS.keys())
selected_club = st.radio(
    "Select club",
    clubs,
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────────────
with st.spinner(f"Loading fan intelligence for {selected_club}..."):
    data = get_full_club_data(selected_club)

kpis = data["kpis"]
sentiment = data["sentiment"]
content = data["content"]
tickets = data["tickets"]
trend = data["trend"]
signals = data["signals"]
sources = data["data_sources"]

# ── Data source legend ───────────────────────────────────────────────────────
src_html = "<div style='margin-bottom:16px'>"
src_html += "<span style='font-size:10px;color:#6b7280;margin-right:8px'>Data sources:</span>"
src_html += f"<span class='data-pill {'pill-live' if sources['sentiment'] == 'live' else 'pill-sim'}'>{'⬤ Live' if sources['sentiment'] == 'live' else '◯ Sim'} Reddit sentiment</span>"
src_html += f"<span class='data-pill {'pill-live' if sources['content'] == 'live' else 'pill-sim'}'>{'⬤ Live' if sources['content'] == 'live' else '◯ Sim'} YouTube</span>"
src_html += "<span class='data-pill pill-sim'>◯ Sim Ticketing</span>"
src_html += "<span class='data-pill pill-sim'>◯ Sim X/TikTok</span>"
src_html += "</div>"
st.markdown(src_html, unsafe_allow_html=True)

# ── KPI row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

def kpi_card(col, label, value, delta, direction):
    delta_class = {"up": "kpi-delta-up", "down": "kpi-delta-down", "flat": "kpi-delta-flat"}[direction]
    arrow = {"up": "▲", "down": "▼", "flat": "—"}[direction]
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="{delta_class}">{arrow} {delta}</div>
        </div>
        """, unsafe_allow_html=True)

sent_dir = "up" if kpis["sentiment_score"] >= 65 else "down"
kpi_card(k1, "Sentiment Score", kpis["sentiment_score"], f"{kpis['sentiment_score'] - 65:+d} vs league avg", sent_dir)
kpi_card(k2, "Content Reach", kpis["content_reach"], "YouTube — last 8 videos", "flat")
kpi_card(k3, "Ticket Demand Index", kpis["demand_index"], "Next 3 fixtures", "up" if kpis["demand_index"] >= 0.75 else "flat")
kpi_card(k4, "Risk Alerts", kpis["risk_alerts"], "Signals requiring action", "down" if kpis["risk_alerts"] > 1 else "flat")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Main panels ──────────────────────────────────────────────────────────────
left, right = st.columns([2, 1])

with left:
    # Sentiment trend chart
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Cross-channel sentiment · 14 days</div>', unsafe_allow_html=True)
    
    fig = go.Figure()
    colors = {"twitter": "#3d9cf0", "instagram": "#c8f135", "youtube": "#f59e0b", "reddit": "#ef4444"}
    dashes = {"twitter": "solid", "instagram": "solid", "youtube": "dash", "reddit": "dot"}
    
    for channel, color in colors.items():
        fig.add_trace(go.Scatter(
            x=trend["dates"],
            y=trend[channel],
            name=channel.capitalize(),
            line=dict(color=color, width=2, dash=dashes[channel]),
            mode="lines",
        ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=220,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            orientation="h", y=-0.15, x=0,
            font=dict(color="#6b7280", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=True, gridcolor="#1f2937", tickfont=dict(color="#6b7280", size=10),
            showline=False, tickangle=0,
            nticks=7,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#1f2937", tickfont=dict(color="#6b7280", size=10),
            range=[30, 100], showline=False,
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Sentiment breakdown bars
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Sentiment breakdown by channel</div>', unsafe_allow_html=True)
    
    channels = ["Twitter / X", "Instagram", "YouTube", "Reddit", "Ticket Reviews"]
    ch_scores = [
        int(kpis["sentiment_score"] * 0.95),
        int(kpis["sentiment_score"] * 1.08),
        int(kpis["sentiment_score"] * 0.92),
        sentiment["score"],
        int(kpis["sentiment_score"] * 0.82),
    ]
    ch_colors = ["#3d9cf0", "#c8f135", "#f59e0b", "#ef4444", "#a78bfa"]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=ch_scores,
        y=channels,
        orientation="h",
        marker=dict(color=ch_colors),
        text=[f"{s}" for s in ch_scores],
        textposition="outside",
        textfont=dict(color="#e8eaf0", size=11),
    ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=200,
        margin=dict(l=0, r=40, t=0, b=0),
        xaxis=dict(range=[0, 110], showgrid=False, showticklabels=False),
        yaxis=dict(tickfont=dict(color="#6b7280", size=11)),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    # Sentiment summary
    st.markdown(f"""
    <div class="panel">
        <div class="panel-title">Sentiment summary</div>
        <div style="display:flex;gap:8px;margin-bottom:12px">
            <div style="flex:1;background:#13161d;border-radius:6px;padding:10px;text-align:center">
                <div style="font-size:10px;color:#22c55e;margin-bottom:3px">POSITIVE</div>
                <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#22c55e">{sentiment['positive_pct']}%</div>
            </div>
            <div style="flex:1;background:#13161d;border-radius:6px;padding:10px;text-align:center">
                <div style="font-size:10px;color:#6b7280;margin-bottom:3px">NEUTRAL</div>
                <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#6b7280">{sentiment['neutral_pct']}%</div>
            </div>
            <div style="flex:1;background:#13161d;border-radius:6px;padding:10px;text-align:center">
                <div style="font-size:10px;color:#ef4444;margin-bottom:3px">NEGATIVE</div>
                <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#ef4444">{sentiment['negative_pct']}%</div>
            </div>
        </div>
        <div style="font-size:10px;color:#6b7280">Based on {sentiment['post_count']} posts analysed · Reddit + simulated channels</div>
    </div>
    """, unsafe_allow_html=True)

    # Fan signals
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Fan intelligence signals</div>', unsafe_allow_html=True)
    
    priority_class = {"HIGH": "signal-high", "MED": "signal-med", "OPT": "signal-opt"}
    for sig in signals:
        cls = priority_class.get(sig["priority"], "signal-opt")
        st.markdown(f"""
        <div class="signal-item {cls}">
            <div class="signal-title">
                <span class="signal-badge">{sig['priority']}</span>
                {sig['title']}
            </div>
            <div class="signal-desc">{sig['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Bottom row ───────────────────────────────────────────────────────────────
b1, b2 = st.columns([1, 1])

with b1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Top content · YouTube</div>', unsafe_allow_html=True)
    
    for v in content["top_videos"][:4]:
        views_fmt = f"{v['views']/1_000_000:.1f}M" if v["views"] >= 1_000_000 else f"{v['views']//1000}K"
        st.markdown(f"""
        <div class="video-item">
            <div>
                <div class="video-title">{v['title'][:52]}{"..." if len(v['title']) > 52 else ""}</div>
                <div class="video-meta">{v['published']}</div>
            </div>
            <div class="video-views">{views_fmt}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with b2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Ticket demand · Next 3 fixtures</div>', unsafe_allow_html=True)
    
    fix_df = pd.DataFrame(tickets["fixtures"])
    if not fix_df.empty:
        fix_df["Capacity %"] = fix_df["att_pct"]
        
        fig3 = go.Figure()
        bar_colors = ["#c8f135" if p >= 80 else "#3d9cf0" if p >= 60 else "#ef4444" 
                      for p in fix_df["att_pct"]]
        labels = [f"{'🏠 ' if r['home'] else '✈ '}{r['opponent']}" for _, r in fix_df.iterrows()]
        
        fig3.add_trace(go.Bar(
            x=fix_df["att_pct"],
            y=labels,
            orientation="h",
            marker=dict(color=bar_colors),
            text=[f"{p}%" for p in fix_df["att_pct"]],
            textposition="outside",
            textfont=dict(color="#e8eaf0", size=11),
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=180,
            margin=dict(l=0, r=40, t=0, b=0),
            xaxis=dict(range=[0, 115], showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(color="#6b7280", size=11)),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        
        for _, row in fix_df.iterrows():
            pct = row["att_pct"]
            vel_color = "#22c55e" if "fast" in row["velocity"].lower() else "#3d9cf0" if "Rising" in row["velocity"] else "#6b7280"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:3px">
                <span>{'🏠' if row['home'] else '✈'} {row['opponent']} · {row['date']}</span>
                <span style="color:{vel_color}">{row['velocity']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footnote">
    FanIntel WSL · Prototype built for Two Circles pitch · 
    Live: YouTube + Reddit · Simulated: X, TikTok, Ticketing · 
    Not production data
</div>
""", unsafe_allow_html=True)
