import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from data import get_full_club_data, get_claude_recommendation, WSL_CLUBS, WSL_LEAGUE_CONTEXT

st.set_page_config(page_title="WSL Fan Intelligence | Two Circles Prototype",
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

# ── Header ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([5,1])
with c1:
    st.markdown("""
    <div style="margin-bottom:4px">
        <span style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#c8f135;letter-spacing:-1px">FanIntel</span>
        <span style="font-family:'Syne',sans-serif;font-size:28px;font-weight:400;color:#4b5563"> / WSL Edition</span>
    </div>
    <div style="font-size:11px;color:#6b7280;letter-spacing:.04em">
        Women's Super League · 2024–25 · Fan Intelligence & Risk Engine · Prototype for Two Circles
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

kpis    = d["kpis"]
sent    = d["sentiment"]
content = d["content"]
tickets = d["tickets"]
trend   = d["trend"]
signals = d["signals"]
risk    = d["risk_data"]
league  = d["league"]
form    = d["form"]
sources = d["data_sources"]
cohorts = d["cohorts"]

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
    "#e8eaf0", "#22c55e" if kpis["demand_index"]>=.75 else "#f59e0b"), unsafe_allow_html=True)
with k4: st.markdown(kpi_html("Fan Risk Score", f"{kpis['overall_risk']}/100",
    f"{'🔴 High risk' if kpis['overall_risk']>=60 else '🟡 Medium risk' if kpis['overall_risk']>=35 else '🟢 Low risk'}",
    risk_color, risk_color), unsafe_allow_html=True)
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
                <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:700;color:{risk_c}">{fr['risk_score']}</div>
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
        <div style="margin-bottom:12px">{''.join(form_pill(r) for r in form)}</div>
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
            <div style="font-size:9px;color:{risk_c};margin-bottom:8px;letter-spacing:.05em">{risk_label}</div>
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

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-size:10px;color:#374151;text-align:center;padding:20px 0 8px;border-top:1px solid #1f2937;margin-top:16px">
    FanIntel WSL · Built for Two Circles pitch · May 2025 ·
    Live: YouTube + Reddit · Simulated: X, TikTok, Ticketing · Not production data
</div>""", unsafe_allow_html=True)
