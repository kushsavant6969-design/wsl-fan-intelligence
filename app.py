import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os, sys, io, random, math
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from data import get_full_club_data, get_claude_recommendation, WSL_CLUBS, WSL_LEAGUE_CONTEXT, PLAYER_DATA, compute_fan_risk_score
from csv_processor import (
    detect_columns, build_csv_data_dict, check_features, is_full_schema,
    CANONICAL_COLUMNS, _pdf_safe,
)
import base64

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

# ── Player Welfare: data generation ─────────────────────────────────────────

_WELFARE_TEMPLATES = [
    # Threats
    {"text": "Watch your back {player}, you don't belong in this league", "category": "Threat", "base_score": 92},
    {"text": "Hope something bad happens to {player} after what she did", "category": "Threat", "base_score": 88},
    {"text": "{player} better not show up to the next game, just saying", "category": "Threat", "base_score": 85},
    {"text": "Someone needs to sort {player} out for real", "category": "Threat", "base_score": 89},
    # Slurs
    {"text": "Can't believe they let {player} play, absolute [slur removed]", "category": "Slur", "base_score": 94},
    {"text": "{player} is a [slur] and shouldn't be in women's football", "category": "Slur", "base_score": 96},
    {"text": "That {player} [slur] deserved to miss that penalty lmao", "category": "Slur", "base_score": 91},
    # Identity attacks
    {"text": "{player} shouldn't be playing, women like her ruin the sport", "category": "Identity Attack", "base_score": 78},
    {"text": "No wonder {player} plays like that, they're all the same tbh", "category": "Identity Attack", "base_score": 81},
    {"text": "{player} and her type have no place in sport", "category": "Identity Attack", "base_score": 84},
    {"text": "The problem with {player} is exactly what's wrong with this generation", "category": "Identity Attack", "base_score": 76},
    # Abuse
    {"text": "{player} is genuinely pathetic, absolute fraud of a footballer", "category": "Abuse", "base_score": 62},
    {"text": "Overrated garbage, {player} should be dropped permanently", "category": "Abuse", "base_score": 55},
    {"text": "{player} is embarrassing herself and this club every single game", "category": "Abuse", "base_score": 60},
    {"text": "lol {player} can't even trap a ball, waste of a shirt", "category": "Abuse", "base_score": 50},
    {"text": "{player} is the worst signing in WSL history, pathetic", "category": "Abuse", "base_score": 58},
    {"text": "Honestly {player} just give up, you're not good enough", "category": "Abuse", "base_score": 54},
]

_FAKE_ACCOUNTS = [
    "anon_hater_88", "footy_troll_uk", "burner_fc_2024", "real_talk_777", "shadow_lad_99",
    "hate_brigade_x", "keyboard_warrior23", "dark_footy_fan", "anon_rage_4ever", "troll_king_wsl",
    "faceless_critic", "rage_merchant_7", "hater_of_wsl", "burner_acc_2025", "shadow_menace_fc",
    "notmyrealname99", "anon_strike_88", "pure_troll_01", "hidden_user_x12", "footy_rager_uk",
]

def _generate_welfare_data(club_name: str):
    rng = random.Random(hash(club_name) % (2**31))
    players = [p["name"] for p in PLAYER_DATA.get(club_name, PLAYER_DATA.get("WSL Overall", []))]
    if not players:
        players = ["Player A", "Player B", "Player C"]

    today = datetime(2025, 5, 1)
    # Simulate match days in the last 30 days
    match_days = [(today - timedelta(days=d)).date() for d in [3, 10, 17, 24]]

    platforms = ["Twitter/X", "Instagram", "YouTube"]
    records = []
    n = rng.randint(110, 160)
    for _ in range(n):
        tmpl = rng.choice(_WELFARE_TEMPLATES)
        player = rng.choice(players)
        days_ago = rng.choices(
            range(30),
            weights=[max(1, 15 - abs(d - md.day % 30)) for d in range(30) for md in match_days[:1]],
            k=1
        )[0]
        # Spike posts near match days
        near_match = any(abs(days_ago - (today - timedelta(days=0)).day + md.day) < 2 for md in match_days)
        post_date = today - timedelta(days=days_ago, hours=rng.randint(0, 23))
        score = min(100, tmpl["base_score"] + rng.randint(-8, 8) + (5 if near_match else 0))
        severity = "HIGH" if score >= 80 else "MED" if score >= 55 else "LOW"
        platform = rng.choices(platforms, weights=[55, 30, 15])[0]
        account = rng.choice(_FAKE_ACCOUNTS) + str(rng.randint(10, 99))
        records.append({
            "timestamp": post_date,
            "player": player,
            "platform": platform,
            "category": tmpl["category"],
            "text": tmpl["text"].format(player=player.split()[0]),
            "toxicity_score": score,
            "severity": severity,
            "account": account,
        })

    df = pd.DataFrame(records).sort_values("timestamp", ascending=False).reset_index(drop=True)
    return df, [md.strftime("%Y-%m-%d") for md in match_days]


def _render_player_welfare(club_name: str):
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="background:#1f0a0a;border:1px solid #ef444440;border-radius:8px;padding:8px 16px;margin-bottom:18px">'
        '<span style="font-size:10px;color:#ef4444">⚠ SIMULATED DATA — </span>'
        '<span style="font-size:10px;color:#6b7280">All social posts below are synthetic and generated for demonstration purposes only. '
        'YouTube data is live. This tool is a proof of concept for safeguarding teams.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    df, match_days = _generate_welfare_data(club_name)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total = len(df)
    high_count = (df["severity"] == "HIGH").sum()
    players_targeted = df["player"].nunique()
    accounts_flagged = df["account"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_html("Total Flagged Posts", str(total), "Last 30 days", color="#ef4444"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_html("High Severity", str(high_count), f"{round(high_count/total*100)}% of total", color="#ef4444"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_html("Players Targeted", str(players_targeted), "Unique individuals", color="#f59e0b"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_html("Flagged Accounts", str(accounts_flagged), "Unique abusive accounts", color="#f59e0b"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Row 1: Player targeting bar + Platform donut ───────────────────────────
    ch1, ch2 = st.columns([3, 2])

    with ch1:
        st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Players Most Targeted</div>', unsafe_allow_html=True)
        player_counts = df.groupby("player").size().sort_values(ascending=True)
        fig_players = go.Figure(go.Bar(
            x=player_counts.values,
            y=player_counts.index,
            orientation="h",
            marker_color="#ef4444",
            marker_line_width=0,
        ))
        fig_players.update_layout(
            paper_bgcolor="#13161d", plot_bgcolor="#13161d",
            margin=dict(l=0, r=10, t=10, b=10),
            height=260,
            xaxis=dict(showgrid=False, color="#4b5563", tickfont=dict(size=10, color="#6b7280")),
            yaxis=dict(showgrid=False, color="#4b5563", tickfont=dict(size=10, color="#9ca3af")),
            font=dict(family="DM Mono, monospace"),
        )
        st.plotly_chart(fig_players, use_container_width=True, key="welfare_player_bar")

    with ch2:
        st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Platform Breakdown</div>', unsafe_allow_html=True)
        plat_counts = df["platform"].value_counts()
        fig_plat = go.Figure(go.Pie(
            labels=plat_counts.index,
            values=plat_counts.values,
            hole=0.55,
            marker_colors=["#ef4444", "#f59e0b", "#3d9cf0"],
            textfont=dict(size=10, family="DM Mono, monospace"),
        ))
        fig_plat.update_layout(
            paper_bgcolor="#13161d",
            margin=dict(l=0, r=0, t=10, b=10),
            height=260,
            legend=dict(font=dict(size=10, color="#6b7280", family="DM Mono, monospace"), bgcolor="rgba(0,0,0,0)"),
            font=dict(family="DM Mono, monospace"),
        )
        st.plotly_chart(fig_plat, use_container_width=True, key="welfare_platform_donut")

    # ── Abuse timeline ─────────────────────────────────────────────────────────
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">30-Day Abuse Timeline</div>', unsafe_allow_html=True)
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date").size().reset_index(name="count")
    daily["date"] = pd.to_datetime(daily["date"])

    fig_tl = go.Figure(go.Scatter(
        x=daily["date"],
        y=daily["count"],
        mode="lines+markers",
        line=dict(color="#ef4444", width=2),
        marker=dict(color="#ef4444", size=5),
        fill="tozeroy",
        fillcolor="rgba(239,68,68,0.08)",
    ))
    for md in match_days:
        fig_tl.add_shape(
            type="line",
            x0=pd.Timestamp(md), x1=pd.Timestamp(md),
            y0=0, y1=1, yref="paper",
            line=dict(dash="dot", color="#f59e0b", width=1),
        )
        fig_tl.add_annotation(
            x=pd.Timestamp(md), y=1, yref="paper",
            text="Match day", showarrow=False,
            font=dict(size=9, color="#f59e0b"),
            xanchor="left", yanchor="top",
        )
    fig_tl.update_layout(
        paper_bgcolor="#13161d", plot_bgcolor="#13161d",
        margin=dict(l=0, r=10, t=20, b=10),
        height=200,
        xaxis=dict(showgrid=False, color="#4b5563", tickfont=dict(size=10, color="#6b7280")),
        yaxis=dict(showgrid=False, color="#4b5563", tickfont=dict(size=10, color="#6b7280"), title="Posts"),
        font=dict(family="DM Mono, monospace"),
    )
    st.plotly_chart(fig_tl, use_container_width=True, key="welfare_timeline")

    # ── Abusive accounts ──────────────────────────────────────────────────────
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Abusive Account Tracker</div>', unsafe_allow_html=True)
    acc_df = (
        df.groupby("account")
        .agg(posts=("text", "count"), avg_toxicity=("toxicity_score", "mean"), top_category=("category", lambda x: x.mode()[0]))
        .sort_values("posts", ascending=False)
        .head(8)
        .reset_index()
    )
    acc_df["avg_toxicity"] = acc_df["avg_toxicity"].round(1)

    header_html = (
        '<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1.5fr;gap:6px;'
        'padding:5px 10px;background:#0a0c10;border-radius:5px 5px 0 0;margin-bottom:2px">'
        + ''.join(f'<div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.08em">{h}</div>'
                  for h in ["Account", "Posts", "Avg Score", "Top Category"])
        + '</div>'
    )
    rows_html = ""
    for _, row in acc_df.iterrows():
        sev_c = "#ef4444" if row["avg_toxicity"] >= 80 else "#f59e0b" if row["avg_toxicity"] >= 55 else "#22c55e"
        rows_html += (
            '<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1.5fr;gap:6px;'
            'padding:6px 10px;border-bottom:1px solid #1a1e27">'
            f'<div style="font-size:11px;color:#9ca3af">{row["account"]}</div>'
            f'<div style="font-size:11px;color:#e8eaf0">{row["posts"]}</div>'
            f'<div style="font-size:11px;color:{sev_c};font-weight:600">{row["avg_toxicity"]}</div>'
            f'<div style="font-size:11px;color:#6b7280">{row["top_category"]}</div>'
            '</div>'
        )
    st.markdown(
        card(header_html + rows_html, padding="0", bg="#13161d"),
        unsafe_allow_html=True,
    )

    # ── CSV export ─────────────────────────────────────────────────────────────
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    export_df = df[["timestamp", "platform", "account", "player", "category", "severity", "toxicity_score", "text"]].copy()
    export_df["timestamp"] = export_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    csv_buf = io.StringIO()
    export_df.to_csv(csv_buf, index=False)
    st.download_button(
        label="⬇ Download Abuse Report CSV",
        data=csv_buf.getvalue(),
        file_name=f"welfare_report_{club_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key="welfare_csv_download",
    )


# ── Sponsorship Intelligence ─────────────────────────────────────────────────

_SPONSOR_CATS = [
    {"category": "Sports Apparel",        "fit": "HIGH", "brands": "Nike, Adidas, New Balance",    "reason": "Strong female 18-35 core audience"},
    {"category": "Healthcare / Wellbeing","fit": "HIGH", "brands": "Vitality, Boots, Bupa",         "reason": "Health-conscious fan demographic"},
    {"category": "Financial Services",    "fit": "MED",  "brands": "Barclays, Starling, Monzo",     "reason": "Growing 26-45 high-earning bracket"},
    {"category": "Tech & Productivity",   "fit": "MED",  "brands": "Adobe, Microsoft, Canva",       "reason": "High digital engagement index"},
    {"category": "Food & Beverage",       "fit": "LOW",  "brands": "Lucozade, Greggs, Uber Eats",   "reason": "Matchday concession opportunity"},
]

def _gen_sponsorship_data(club_name: str, d: dict) -> dict:
    rng = random.Random(hash(club_name + "sponsor2025") % (2**31))
    sentiment = d["kpis"]["sentiment_score"]
    demand    = d["kpis"]["demand_index"] * 100
    risk      = d["kpis"]["overall_risk"]
    pitch_score = min(100, max(30, round(sentiment * 0.35 + demand * 0.30 + (100 - risk) * 0.25 + rng.uniform(0, 10))))

    age_w = [rng.randint(18, 32), rng.randint(28, 40), rng.randint(18, 28), rng.randint(8, 18)]
    total_a = sum(age_w)
    age_pcts = [round(w / total_a * 100) for w in age_w]

    female_pct = rng.randint(52, 68)
    other_pct  = rng.randint(2, 5)
    male_pct   = 100 - female_pct - other_pct

    country_names = ["England", "USA", "Germany", "Spain", "Australia"]
    country_pcts  = sorted([rng.randint(5, 50) for _ in country_names], reverse=True)
    total_c = sum(country_pcts)
    country_pcts  = [round(p / total_c * 100) for p in country_pcts]

    base_avg = round(demand * 0.4 + sentiment * 0.3 + (100 - risk) * 0.3)
    scores = [max(0, min(100, rng.gauss(base_avg, 18))) for _ in range(300)]

    segs     = ["Season Ticket", "Regular Fan", "Casual Fan", "Lapsed Fan"]
    seg_comm = [rng.randint(70, 95), rng.randint(50, 75), rng.randint(30, 55), rng.randint(10, 30)]
    seg_size = [rng.randint(8, 18),  rng.randint(25, 40), rng.randint(30, 45), rng.randint(10, 25)]

    return dict(
        pitch_score=pitch_score, age_groups=["18-25","26-35","36-45","46+"],
        age_pcts=age_pcts, female_pct=female_pct, male_pct=male_pct, other_pct=other_pct,
        country_names=country_names, country_pcts=country_pcts,
        scores=scores, base_avg=base_avg,
        segs=segs, seg_comm=seg_comm, seg_size=seg_size,
    )


def _render_sponsorship(club_name: str, d: dict) -> None:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="background:#1c1500;border:1px solid #f59e0b40;border-radius:8px;padding:8px 16px;margin-bottom:18px">'
        '<span style="font-size:10px;color:#f59e0b">◯ SIMULATED — </span>'
        '<span style="font-size:10px;color:#6b7280">Demographic and commercial data is illustrative. '
        'Integrate your CRM for live audience quality scores.</span></div>',
        unsafe_allow_html=True,
    )

    sd = _gen_sponsorship_data(club_name, d)
    ps = sd["pitch_score"]
    ps_color = "#c8f135" if ps >= 75 else "#22c55e" if ps >= 60 else "#f59e0b" if ps >= 45 else "#ef4444"
    ps_label  = "Premium Sponsorship Property" if ps >= 75 else "Strong Audience Proposition" if ps >= 60 else "Emerging Commercial Value" if ps >= 45 else "Developing Audience"
    ps_bg     = "#0d1700" if ps >= 75 else "#0a1f0a" if ps >= 60 else "#1c1500" if ps >= 45 else "#1f0a0a"

    st.markdown(
        f'<div style="background:{ps_bg};border:1px solid {ps_color}40;border-radius:12px;padding:20px 28px;'
        f'margin-bottom:18px;display:flex;align-items:center;gap:28px">'
        f'<div style="text-align:center;min-width:110px">'
        f'<div style="font-size:9px;color:{ps_color};letter-spacing:.1em;margin-bottom:4px;text-transform:uppercase">Sponsorship Pitch Score</div>'
        f'<div style="font-family:Syne,sans-serif;font-size:58px;font-weight:800;color:{ps_color};line-height:1">{ps}</div>'
        f'<div style="font-size:10px;color:#4b5563;margin-top:2px">out of 100</div></div>'
        f'<div style="flex:1">'
        f'<div style="font-size:13px;color:{ps_color};font-weight:600;margin-bottom:6px">{ps_label}</div>'
        f'<div style="background:#0a0c10;border-radius:5px;height:6px;overflow:hidden;margin-bottom:12px">'
        f'<div style="width:{ps}%;height:100%;background:{ps_color};border-radius:5px"></div></div>'
        f'<div style="font-size:11px;color:#6b7280;line-height:1.6">'
        f'Composite of fan sentiment ({d["kpis"]["sentiment_score"]}/100), ticket demand '
        f'({round(d["kpis"]["demand_index"]*100)}%), and risk-adjusted commercial score. '
        f'Benchmarked against WSL average of 58.</div></div></div>',
        unsafe_allow_html=True,
    )

    # ── KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(kpi_html("Female Audience", f"{sd['female_pct']}%", "of total fanbase", "#c8f135"), unsafe_allow_html=True)
    with k2: st.markdown(kpi_html("Core Demo 18-35", f"{sd['age_pcts'][0]+sd['age_pcts'][1]}%", "highest commercial value band", "#22c55e"), unsafe_allow_html=True)
    with k3: st.markdown(kpi_html("Top Market", sd["country_names"][0], f"{sd['country_pcts'][0]}% of audience", "#3d9cf0"), unsafe_allow_html=True)
    with k4: st.markdown(kpi_html("Avg Commercial Score", str(sd["base_avg"]), "fan commercial value index", "#f59e0b"), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Row 1: Gender bar + Country ──
    r1b, r1c = st.columns(2)

    with r1b:
        st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Gender Split</div>', unsafe_allow_html=True)
        genders = ["Female", "Male", "Other"]
        g_vals  = [sd["female_pct"], sd["male_pct"], sd["other_pct"]]
        g_cols  = ["#c8f135", "#3d9cf0", "#6b7280"]
        fig_gen = go.Figure(go.Bar(
            y=genders, x=g_vals, orientation="h",
            marker_color=g_cols, marker_line_width=0,
            text=[f"{v}%" for v in g_vals], textposition="inside",
            textfont=dict(size=11, color="#0a0c10"),
        ))
        fig_gen.update_layout(
            paper_bgcolor="#13161d", plot_bgcolor="#13161d",
            margin=dict(l=0,r=10,t=10,b=10), height=220,
            xaxis=dict(showgrid=False, visible=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=11,color="#9ca3af")),
            font=dict(family="DM Mono, monospace"),
        )
        st.plotly_chart(fig_gen, use_container_width=True, key="sp_gender_bar", config={"displayModeBar":False})

    with r1c:
        st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Top Audience Markets</div>', unsafe_allow_html=True)
        mkt_html = ""
        for cn, cp in zip(sd["country_names"], sd["country_pcts"]):
            mkt_html += (
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
                f'<div style="font-size:11px;color:#9ca3af;min-width:90px">{cn}</div>'
                f'<div style="flex:1;background:#0a0c10;border-radius:3px;height:8px;overflow:hidden">'
                f'<div style="width:{cp}%;height:100%;background:#3d9cf0;border-radius:3px"></div></div>'
                f'<div style="font-size:11px;color:#6b7280;min-width:32px;text-align:right">{cp}%</div></div>'
            )
        st.markdown(card(mkt_html, padding="14px 16px"), unsafe_allow_html=True)

    # ── Audience quality ──
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Audience Quality by Segment</div>', unsafe_allow_html=True)
    seg_colors = ["#c8f135", "#22c55e", "#3d9cf0", "#6b7280"]
    fig_seg = go.Figure(go.Bar(
        y=sd["segs"], x=sd["seg_comm"], orientation="h",
        marker_color=seg_colors, marker_line_width=0,
        text=sd["seg_comm"], textposition="inside",
        textfont=dict(size=11, color="#0a0c10"),
    ))
    fig_seg.update_layout(
        paper_bgcolor="#13161d", plot_bgcolor="#13161d",
        margin=dict(l=0,r=10,t=10,b=10), height=220,
        xaxis=dict(showgrid=False, range=[0,100], tickfont=dict(size=10,color="#6b7280")),
        yaxis=dict(showgrid=False, tickfont=dict(size=11,color="#9ca3af")),
        font=dict(family="DM Mono, monospace"),
    )
    st.plotly_chart(fig_seg, use_container_width=True, key="sp_seg_bar", config={"displayModeBar":False})

    # ── Sponsor recommendations ──
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px">Top Sponsor Category Recommendations</div>', unsafe_allow_html=True)

    fit_colors = {"HIGH": "#22c55e", "MED": "#f59e0b", "LOW": "#6b7280"}
    fit_bg     = {"HIGH": "#052e16", "MED": "#1c1500", "LOW": "#13161d"}
    rec_html   = (
        '<div style="display:grid;grid-template-columns:1.4fr 1fr 2fr 2.5fr;gap:6px;'
        'padding:5px 12px;background:#0a0c10;border-radius:5px 5px 0 0;margin-bottom:2px">'
        + "".join(f'<div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.08em">{h}</div>'
                  for h in ["Category", "Fit", "Example Brands", "Why"])
        + "</div>"
    )
    for cat in _SPONSOR_CATS:
        fc = fit_colors.get(cat["fit"], "#6b7280")
        fb = fit_bg.get(cat["fit"], "#13161d")
        rec_html += (
            f'<div style="display:grid;grid-template-columns:1.4fr 1fr 2fr 2.5fr;gap:6px;'
            f'padding:8px 12px;border-bottom:1px solid #1a1e27;align-items:center">'
            f'<div style="font-size:11px;color:#e8eaf0">{cat["category"]}</div>'
            f'<div><span style="background:{fb};color:{fc};border:1px solid {fc};font-size:9px;padding:2px 8px;border-radius:8px">{cat["fit"]}</span></div>'
            f'<div style="font-size:10px;color:#6b7280">{cat["brands"]}</div>'
            f'<div style="font-size:10px;color:#4b5563">{cat["reason"]}</div></div>'
        )
    st.markdown(card(rec_html, padding="0", bg="#13161d"), unsafe_allow_html=True)

    # ── PDF download ──
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    try:
        from fpdf import FPDF
        def _ps(t):
            return str(t).replace("\u2014"," - ").replace("\u2013","-").replace("\u2022","-").encode("latin-1",errors="replace").decode("latin-1")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(10, 12, 16)
        pdf.rect(0, 0, 210, 297, "F")
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(200, 241, 53)
        pdf.cell(0, 12, f"FanIntel - Sponsorship Deck", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(0, 8, _ps(f"{club_name} - WSL Edition - {datetime.now().strftime('%B %Y')}"), ln=True)
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(200, 241, 53)
        pdf.cell(0, 10, f"Pitch Score: {ps}/100 - {ps_label}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(156, 163, 175)
        pdf.cell(0, 7, _ps(f"Female audience: {sd['female_pct']}%  |  Core 18-35: {sd['age_pcts'][0]+sd['age_pcts'][1]}%  |  Avg commercial score: {sd['base_avg']}"), ln=True)
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(200, 241, 53)
        pdf.cell(0, 8, "Sponsor Recommendations", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for cat in _SPONSOR_CATS:
            pdf.set_text_color(232, 234, 240)
            pdf.cell(0, 6, _ps(f"[{cat['fit']}] {cat['category']} - {cat['brands']}"), ln=True)
            pdf.set_text_color(107, 114, 128)
            pdf.cell(0, 5, _ps(f"     {cat['reason']}"), ln=True)
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(75, 85, 99)
        pdf.cell(0, 6, _ps("CONFIDENTIAL - Generated by FanIntel WSL Edition - Illustrative data only"), ln=True)
        pdf_bytes = pdf.output()
        st.download_button(
            label="⬇ Download Sponsorship Deck PDF",
            data=bytes(pdf_bytes),
            file_name=f"sponsorship_deck_{club_name.replace(' ','_').lower()}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            key="sp_pdf_dl",
        )
    except Exception:
        st.caption("PDF export unavailable — fpdf2 not installed.")


# ── Matchday Intelligence ─────────────────────────────────────────────────────

_MATCHDAY_SEGMENTS = [
    {"name": "Season Ticket",   "avg_spend": 18,  "color": "#c8f135"},
    {"name": "Member",          "avg_spend": 26,  "color": "#22c55e"},
    {"name": "General Admit.",  "avg_spend": 38,  "color": "#3d9cf0"},
    {"name": "Hospitality",     "avg_spend": 95,  "color": "#a78bfa"},
]

def _gen_matchday_data(club_name: str, d: dict) -> dict:
    rng = random.Random(hash(club_name + "matchday2025") % (2**31))
    capacity = WSL_CLUBS.get(club_name, WSL_CLUBS["Arsenal W"])["capacity"]
    fixtures = d["tickets"]["fixtures"][:3]

    seg_splits = [0.35, 0.30, 0.28, 0.07]
    fixture_rev = []
    for f in fixtures:
        att = round(capacity * (f["att_pct"] / 100))
        rev = 0
        seg_revs = []
        for seg, split in zip(_MATCHDAY_SEGMENTS, seg_splits):
            fans = round(att * split)
            r    = fans * seg["avg_spend"]
            seg_revs.append({"segment": seg["name"], "fans": fans, "revenue": r, "avg_spend": seg["avg_spend"], "color": seg["color"]})
            rev += r
        fixture_rev.append({"fixture": f"vs {f['opponent'].replace('Arsenal W','Arsenal').replace('Chelsea W','Chelsea').replace('Man City W','Man City').replace('Brighton W','Brighton').replace('Aston Villa W','Villa')}", "revenue": rev, "att": att, "seg_revs": seg_revs})

    top_revenue_fixture = max(fixture_rev, key=lambda x: x["revenue"])
    top_segment = max(top_revenue_fixture["seg_revs"], key=lambda x: x["revenue"])

    high_potential_fans = round(capacity * rng.uniform(0.12, 0.22))
    convert_pct         = rng.randint(5, 15)
    additional_revenue  = round(high_potential_fans * (convert_pct / 100) * _MATCHDAY_SEGMENTS[2]["avg_spend"])

    windows = ["Pre-match\n-90 to -30min", "Pre-match\n-30 to KO", "Half-time", "Post-match\n0-30min", "Post-match\n30-90min"]
    window_eng = [
        round(rng.uniform(20, 40)),
        round(rng.uniform(55, 80)),
        round(rng.uniform(70, 90)),
        round(rng.uniform(60, 85)),
        round(rng.uniform(25, 45)),
    ]

    hospitality_targets = []
    for i in range(20):
        engagement = rng.randint(72, 98)
        hospitality_targets.append({
            "fan_id": f"FAN-{rng.randint(10000,99999)}",
            "engagement": engagement,
            "last_ticket": f"{rng.randint(6,24)}mo ago",
            "ltv_band": "HIGH" if engagement > 88 else "MED",
            "segment": rng.choice(["Regular Fan", "Lapsed Member", "App User"]),
        })
    hospitality_targets.sort(key=lambda x: x["engagement"], reverse=True)

    return dict(
        fixture_rev=fixture_rev,
        top_revenue_fixture=top_revenue_fixture,
        top_segment=top_segment,
        high_potential_fans=high_potential_fans,
        convert_pct=convert_pct,
        additional_revenue=additional_revenue,
        windows=windows,
        window_eng=window_eng,
        hospitality_targets=hospitality_targets,
        capacity=capacity,
    )


def _render_matchday(club_name: str, d: dict) -> None:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="background:#1c1500;border:1px solid #f59e0b40;border-radius:8px;padding:8px 16px;margin-bottom:18px">'
        '<span style="font-size:10px;color:#f59e0b">◯ SIMULATED — </span>'
        '<span style="font-size:10px;color:#6b7280">Revenue and hospitality data is illustrative. '
        'Integrate ticketing CRM for live figures.</span></div>',
        unsafe_allow_html=True,
    )

    md = _gen_matchday_data(club_name, d)
    top_fix = md["top_revenue_fixture"]
    top_seg = md["top_segment"]
    avg_spend_all = round(sum(s["avg_spend"] * sp for s, sp in zip(_MATCHDAY_SEGMENTS, [0.35, 0.30, 0.28, 0.07])))

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(kpi_html("Est. Revenue / Fixture", f"£{top_fix['revenue']:,.0f}", f"{top_fix['fixture']} · {top_fix['att']:,} fans", "#c8f135"), unsafe_allow_html=True)
    with k2: st.markdown(kpi_html("Top Revenue Segment", top_seg["segment"], f"£{top_seg['revenue']:,.0f} per fixture", "#22c55e"), unsafe_allow_html=True)
    with k3: st.markdown(kpi_html("Avg Spend / Fan", f"£{avg_spend_all}", "blended across segments", "#3d9cf0"), unsafe_allow_html=True)
    with k4: st.markdown(kpi_html("Hospitality Targets", "20", "high-engagement, no recent ticket", "#a78bfa"), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Revenue opportunity callout ──
    st.markdown(
        f'<div style="background:#052e16;border:1px solid #22c55e40;border-radius:10px;padding:14px 20px;margin-bottom:18px">'
        f'<span style="font-size:10px;color:#22c55e;text-transform:uppercase;letter-spacing:.08em">Revenue Opportunity </span>'
        f'<span style="font-size:13px;color:#e8eaf0;font-weight:600"> — Converting {md["convert_pct"]}% of High Potential fans = </span>'
        f'<span style="font-family:Syne,sans-serif;font-size:18px;font-weight:800;color:#c8f135">£{md["additional_revenue"]:,}</span>'
        f'<span style="font-size:11px;color:#6b7280"> additional per fixture</span></div>',
        unsafe_allow_html=True,
    )

    # ── Estimated Revenue by Segment ──
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Estimated Revenue by Segment</div>', unsafe_allow_html=True)
    seg_revs = top_fix["seg_revs"]
    fig_rev = go.Figure(go.Bar(
        y=[s["segment"] for s in seg_revs],
        x=[s["revenue"] for s in seg_revs],
        orientation="h",
        marker_color=[s["color"] for s in seg_revs],
        marker_line_width=0,
        text=[f"£{s['revenue']:,.0f}" for s in seg_revs],
        textposition="inside",
        textfont=dict(size=10, color="#0a0c10"),
    ))
    fig_rev.update_layout(
        paper_bgcolor="#13161d", plot_bgcolor="#13161d",
        margin=dict(l=0,r=10,t=10,b=10), height=230,
        xaxis=dict(showgrid=False, tickfont=dict(size=10,color="#6b7280"),
                   tickprefix="£", tickformat=",.0f"),
        yaxis=dict(showgrid=False, tickfont=dict(size=11,color="#9ca3af")),
        font=dict(family="DM Mono, monospace"),
    )
    st.plotly_chart(fig_rev, use_container_width=True, key="md_rev_bar", config={"displayModeBar":False})


# ── Fan Acquisition Intelligence ──────────────────────────────────────────────

_ACQ_MARKETS = [
    {"country": "United States",    "iso": "USA", "priority": 0, "activation": "Digital-first: TikTok + YouTube highlight clips, partner with NWSL fanbases"},
    {"country": "Germany",          "iso": "DEU", "priority": 0, "activation": "Bundesliga W cross-promotion, German-language content, DFB tie-ins"},
    {"country": "Australia",        "iso": "AUS", "priority": 0, "activation": "Matildas halo effect post-2023 WWC, streaming deal push, timezone-friendly content"},
    {"country": "Spain",            "iso": "ESP", "priority": 0, "activation": "Liga F fan crossover, Instagram-led campaign, Spanish influencer partnerships"},
    {"country": "Netherlands",      "iso": "NLD", "priority": 0, "activation": "OranjeLeeuwinnen connection, Dutch player ambassador content"},
    {"country": "Canada",           "iso": "CAN", "priority": 0, "activation": "CanWNT fan base, membership trial offer, bilingual content"},
    {"country": "Brazil",           "iso": "BRA", "priority": 0, "activation": "Fastest-growing women's football market, YouTube-first content strategy"},
    {"country": "Japan",            "iso": "JPN", "priority": 0, "activation": "Nadeshiko crossover, merchandise appeal, streaming subscription push"},
]

_AGE_TARGETS = {
    "current": [22, 35, 28, 15],
    "target":  [30, 32, 24, 14],
    "labels":  ["18-25", "26-35", "36-45", "46+"],
}

def _gen_acquisition_data(club_name: str, d: dict) -> dict:
    rng = random.Random(hash(club_name + "acquire2025") % (2**31))
    sentiment = d["kpis"]["sentiment_score"]
    demand    = d["kpis"]["demand_index"] * 100

    markets = []
    for i, m in enumerate(_ACQ_MARKETS):
        base   = max(20, min(95, round(sentiment * 0.3 + demand * 0.2 + rng.randint(20, 55))))
        decay  = max(0, (i // 2) * rng.randint(5, 12))
        priority = max(20, base - decay + rng.randint(-5, 5))
        fan_count = rng.randint(800, 8000) - i * rng.randint(50, 400)
        eng  = round(rng.uniform(30, 85))
        comm = round(rng.uniform(25, 80))
        markets.append({**m, "priority": priority, "fan_count": max(300, fan_count), "engagement": eng, "commercial": comm})
    markets.sort(key=lambda x: x["priority"], reverse=True)

    age_gap_delta = [_AGE_TARGETS["target"][i] - _AGE_TARGETS["current"][i] + rng.randint(-3, 3)
                     for i in range(4)]

    choropleth_iso   = [m["iso"] for m in markets]
    choropleth_vals  = [m["priority"] for m in markets]
    choropleth_text  = [m["country"] for m in markets]

    return dict(markets=markets, age_gap_delta=age_gap_delta,
                choropleth_iso=choropleth_iso, choropleth_vals=choropleth_vals,
                choropleth_text=choropleth_text)


def _render_fan_acquisition(club_name: str, d: dict) -> None:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="background:#1c1500;border:1px solid #f59e0b40;border-radius:8px;padding:8px 16px;margin-bottom:18px">'
        '<span style="font-size:10px;color:#f59e0b">◯ SIMULATED — </span>'
        '<span style="font-size:10px;color:#6b7280">Market priority scores are illustrative. '
        'Connect to your geo fan data for live acquisition intelligence.</span></div>',
        unsafe_allow_html=True,
    )

    aq = _gen_acquisition_data(club_name, d)
    top5 = aq["markets"][:5]

    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(kpi_html("Top Priority Market", top5[0]["country"], f"Priority score: {top5[0]['priority']}", "#c8f135"), unsafe_allow_html=True)
    with k2: st.markdown(kpi_html("Markets Analysed", str(len(aq["markets"])), "across 8 key territories", "#22c55e"), unsafe_allow_html=True)
    with k3: st.markdown(kpi_html("Biggest Age Gap", "18-25", f"{abs(aq['age_gap_delta'][0]):+}pp vs target", "#f59e0b"), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── World map ──
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Global Fan Acquisition Priority Map</div>', unsafe_allow_html=True)
    fig_map = go.Figure(go.Choropleth(
        locations=aq["choropleth_iso"],
        z=aq["choropleth_vals"],
        text=aq["choropleth_text"],
        colorscale=[[0,"#13161d"],[0.3,"#1a4020"],[0.6,"#22c55e"],[1.0,"#c8f135"]],
        zmin=0, zmax=100,
        marker_line_color="#2a2f3d", marker_line_width=0.5,
        colorbar=dict(
            title=dict(text="Priority", font=dict(color="#6b7280", size=10)),
            tickfont=dict(color="#6b7280", size=10),
            bgcolor="#13161d", bordercolor="#2a2f3d",
            thickness=12,
        ),
        hovertemplate="<b>%{text}</b><br>Priority: %{z}<extra></extra>",
    ))
    fig_map.update_geos(
        bgcolor="#0a0c10", landcolor="#1f2937", oceancolor="#0a0c10",
        showframe=False, showcoastlines=True, coastlinecolor="#2a2f3d",
        projection_type="natural earth",
    )
    fig_map.update_layout(
        paper_bgcolor="#13161d", geo=dict(bgcolor="#0a0c10"),
        margin=dict(l=0,r=0,t=0,b=0), height=340,
        font=dict(family="DM Mono, monospace", color="#6b7280"),
    )
    st.plotly_chart(fig_map, use_container_width=True, key="aq_map", config={"displayModeBar":False})

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── Acquisition Priority Score by Market ──
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Acquisition Priority Score by Market</div>', unsafe_allow_html=True)
    bar_colors = ["#c8f135" if m["priority"] >= 70 else "#22c55e" if m["priority"] >= 55 else "#3d9cf0" for m in aq["markets"]]
    fig_pri = go.Figure(go.Bar(
        y=[m["country"] for m in reversed(aq["markets"])],
        x=[m["priority"] for m in reversed(aq["markets"])],
        orientation="h",
        marker_color=list(reversed(bar_colors)),
        marker_line_width=0,
        text=[str(m["priority"]) for m in reversed(aq["markets"])],
        textposition="inside",
        textfont=dict(size=10, color="#0a0c10"),
    ))
    fig_pri.update_layout(
        paper_bgcolor="#13161d", plot_bgcolor="#13161d",
        margin=dict(l=0,r=10,t=10,b=10), height=280,
        xaxis=dict(showgrid=False, range=[0,100], tickfont=dict(size=10,color="#6b7280")),
        yaxis=dict(showgrid=False, tickfont=dict(size=10,color="#9ca3af")),
        font=dict(family="DM Mono, monospace"),
    )
    st.plotly_chart(fig_pri, use_container_width=True, key="aq_pri_bar", config={"displayModeBar":False})

    # ── Demographic gap analysis ──
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Demographic Gap Analysis — Current vs Target Age Mix</div>', unsafe_allow_html=True)
    age_labels  = _AGE_TARGETS["labels"]
    current_pct = _AGE_TARGETS["current"]
    target_pct  = _AGE_TARGETS["target"]
    fig_age = go.Figure()
    fig_age.add_trace(go.Bar(name="Current", x=age_labels, y=current_pct,
                             marker_color="#3d9cf0", marker_line_width=0))
    fig_age.add_trace(go.Bar(name="Target",  x=age_labels, y=target_pct,
                             marker_color="#c8f135", marker_line_width=0))
    fig_age.update_layout(
        paper_bgcolor="#13161d", plot_bgcolor="#13161d",
        margin=dict(l=0,r=10,t=10,b=10), height=200, barmode="group",
        xaxis=dict(showgrid=False, tickfont=dict(size=11,color="#9ca3af")),
        yaxis=dict(showgrid=False, tickfont=dict(size=10,color="#6b7280"),
                   title=dict(text="% of fanbase", font=dict(size=10,color="#4b5563"))),
        legend=dict(font=dict(size=10,color="#9ca3af",family="DM Mono, monospace"),bgcolor="rgba(0,0,0,0)"),
        font=dict(family="DM Mono, monospace"),
    )
    st.plotly_chart(fig_age, use_container_width=True, key="aq_age_gap", config={"displayModeBar":False})

    # ── Top 5 markets activation cards ──
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px">Top 5 Target Markets — Activation Strategies</div>', unsafe_allow_html=True)
    for i, m in enumerate(top5):
        rank_c = "#c8f135" if i == 0 else "#22c55e" if i == 1 else "#3d9cf0"
        st.markdown(
            f'<div style="background:#13161d;border:1px solid #2a2f3d;border-radius:8px;padding:12px 16px;margin-bottom:8px;display:flex;align-items:flex-start;gap:16px">'
            f'<div style="font-family:Syne,sans-serif;font-size:22px;font-weight:800;color:{rank_c};min-width:28px;line-height:1.2">#{i+1}</div>'
            f'<div style="flex:1">'
            f'<div style="font-size:13px;color:#e8eaf0;font-weight:600;margin-bottom:4px">{m["country"]}'
            f'<span style="font-size:10px;color:{rank_c};background:#0a1700;border:1px solid {rank_c}40;'
            f'padding:2px 8px;border-radius:8px;margin-left:10px">Priority {m["priority"]}</span></div>'
            f'<div style="font-size:11px;color:#6b7280;line-height:1.6">{m["activation"]}</div></div></div>',
            unsafe_allow_html=True,
        )


# ── Badge helpers ─────────────────────────────────────────────────────────────
def source_badge(from_data: bool) -> str:
    if from_data:
        return '<span style="background:#052e16;color:#22c55e;border:1px solid #166534;font-size:8px;padding:2px 7px;border-radius:8px;margin-left:6px">From your data</span>'
    return '<span style="background:#1c1500;color:#f59e0b;border:1px solid #92400e;font-size:8px;padding:2px 7px;border-radius:8px;margin-left:6px">Modelled</span>'


def feature_gate_placeholder(feature_name: str, needed_cols: list) -> None:
    cols_str = ", ".join(needed_cols)
    st.markdown(
        f'<div style="background:#0d1117;border:1px dashed #2a2f3d;border-radius:10px;padding:22px 24px;margin-bottom:14px;text-align:center">'
        f'<div style="font-size:22px;margin-bottom:8px">🔒</div>'
        f'<div style="font-size:12px;color:#4b5563;margin-bottom:4px">{feature_name} — column not detected</div>'
        f'<div style="font-size:10px;color:#374151">Upload a CSV containing <span style="color:#c8f135">{cols_str}</span> to unlock this module</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── WSL Context Panel ─────────────────────────────────────────────────────────
def render_wsl_context_panel() -> None:
    st.markdown("<hr style='border-color:#1f2937;margin:16px 0 16px'>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:12px">'
        'WSL Fan Intelligence · context &amp; benchmarks'
        '</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    panels = [
        {
            "icon": "📊",
            "label": "Avidity Gap",
            "stat":  "36% vs 61%",
            "stat_color": "#f59e0b",
            "body": (
                "Women's football fan avidity sits at <strong style='color:#f59e0b'>36%</strong> "
                "vs <strong style='color:#22c55e'>61%</strong> for men's. "
                "Closing this gap is the single biggest commercial opportunity in British sport right now."
            ),
        },
        {
            "icon": "💰",
            "label": "Revenue Concentration",
            "stat":  "20% → 66%",
            "stat_color": "#c8f135",
            "body": (
                "The top <strong style='color:#c8f135'>20%</strong> of WSL fans drive "
                "<strong style='color:#c8f135'>two-thirds</strong> of total club revenue. "
                "Identifying and protecting this cohort is the #1 commercial priority."
            ),
        },
        {
            "icon": "🎯",
            "label": "Platform Mission",
            "stat":  "Data → Decisions",
            "stat_color": "#3d9cf0",
            "body": (
                "FanIntel connects fan behaviour data to commercial outcomes. "
                "Every signal surfaces a recommended action — so clubs can act on insight, not instinct."
            ),
        },
    ]
    for i, p in enumerate(panels):
        with cols[i]:
            st.markdown(
                f'<div style="background:#0d1117;border:1px solid #1a1e27;border-top:2px solid {p["stat_color"]};'
                f'border-radius:8px;padding:16px 18px;height:100%">'
                f'<div style="font-size:18px;margin-bottom:6px">{p["icon"]}</div>'
                f'<div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">{p["label"]}</div>'
                f'<div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:{p["stat_color"]};margin-bottom:8px">{p["stat"]}</div>'
                f'<div style="font-size:11px;color:#6b7280;line-height:1.6">{p["body"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Upload Screen ─────────────────────────────────────────────────────────────
def _get_sample_csv_b64() -> str:
    """Return base64-encoded sample CSV for download button."""
    import io, random as rnd
    rng = rnd.Random(42)
    players = ["Sam Kerr", "Vivianne Miedema", "Beth Mead", "Lauren Hemp",
               "Rachel Daly", "Chloe Kelly", "Millie Bright", "Erin Cuthbert"]
    channels = ["Email", "SMS", "App", "Social", "Post"]
    memberships = ["Season Ticket", "Member", "General Admission", "Hospitality", "Lapsed"]
    postcodes = ["M1", "M2", "M3", "N1", "N2", "SE1", "SW1", "E1", "W1", "EC1",
                 "B1", "B2", "LS1", "LS2", "L1", "L2", "BS1", "CF1", "EH1"]
    genders = ["Female", "Male", "Non-binary", "Prefer not to say"]

    rows = []
    for i in range(1, 201):
        age = rng.randint(16, 72)
        last_days_ago = rng.randint(0, 730)
        last_dt = (datetime.now() - timedelta(days=last_days_ago)).strftime("%Y-%m-%d")
        tkts = rng.randint(0, 18) if last_days_ago < 365 else rng.randint(0, 3)
        spend = round(tkts * rng.uniform(12, 95) + rng.uniform(0, 120), 2)
        eng = round(rng.uniform(0.05, 0.98), 2)
        rows.append({
            "Fan_ID":            f"WSL-{i:04d}",
            "Age":               age,
            "Gender":            rng.choice(genders),
            "Last_Attended":     last_dt,
            "Tickets_Purchased": tkts,
            "Spend":             spend,
            "Favourite_Player":  rng.choice(players),
            "Engagement_Score":  eng,
            "Channel_Preference":rng.choice(channels),
            "Membership_Type":   rng.choice(memberships),
            "Postcode_District": rng.choice(postcodes),
        })
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    return base64.b64encode(buf.getvalue().encode()).decode()


def render_upload_screen() -> None:
    st.markdown("""
    <div style="background:#0d1117;border:1px solid #c8f13540;border-radius:12px;padding:28px 32px;margin-bottom:24px">
        <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:#c8f135;margin-bottom:8px">
            📂 Upload your fan database
        </div>
        <div style="font-size:12px;color:#6b7280;line-height:1.7;max-width:640px">
            FanIntel turns your fan data into commercial decisions.
            Upload a CSV with any fan columns — we'll auto-detect what you have
            and unlock the relevant intelligence modules. No template required.
        </div>
    </div>""", unsafe_allow_html=True)

    up_col, dl_col = st.columns([3, 1])
    with up_col:
        uploaded = st.file_uploader(
            "Drop your CSV here or click Browse",
            type=["csv"],
            key="csv_uploader_main",
            label_visibility="collapsed",
        )
    with dl_col:
        csv_b64 = _get_sample_csv_b64()
        st.markdown(
            f'<a href="data:text/csv;base64,{csv_b64}" download="wsl_sample_fans.csv" '
            f'style="display:block;text-align:center;background:#13161d;border:1px solid #2a2f3d;'
            f'color:#9ca3af;font-size:11px;padding:10px 14px;border-radius:6px;text-decoration:none;margin-top:4px">'
            f'⬇ Sample CSV (200 fans)</a>',
            unsafe_allow_html=True,
        )

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            col_map = detect_columns(df)
            st.session_state["csv_df"] = df
            st.session_state["csv_col_map"] = col_map
            st.rerun()
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
        return

    # ── Recommended Columns table ──────────────────────────────────────────────
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px">'
        'Recommended columns — what each column unlocks</div>',
        unsafe_allow_html=True,
    )

    col_info = [
        ("Fan_ID",            "Required base for all features",               True),
        ("Age",               "Fan Cohort Breakdown",                         True),
        ("Last_Attended",     "Churn Risk Score + Attendance Prediction",      True),
        ("Tickets_Purchased", "Ticket Demand Index + Fan Risk Score",          True),
        ("Engagement_Score",  "Cross-channel Sentiment Score",                 True),
        ("Spend",             "Commercial Impact Summary + Sponsor Exposure",  False),
        ("Favourite_Player",  "Player Sentiment Intelligence (gated module)",  False),
        ("Channel_Preference","Actionable Campaign Recommendations",           False),
        ("Membership_Type",   "Loyalty Segmentation",                         False),
        ("Postcode_District", "Geographic Fan Analysis",                       False),
        ("Gender",            "Demographic Breakdown",                        False),
    ]

    hdr = (
        '<div style="display:grid;grid-template-columns:1.4fr 2.5fr 90px;gap:8px;'
        'padding:6px 14px;background:#0a0c10;border-radius:5px 5px 0 0;margin-bottom:2px">'
        + "".join(f'<div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.08em">{h}</div>'
                  for h in ["Column", "What it unlocks", "Core"])
        + "</div>"
    )
    rows_html = ""
    for col_name, unlocks, is_core in col_info:
        core_badge = (
            '<span style="background:#052e16;color:#22c55e;border:1px solid #22c55e;font-size:8px;padding:2px 6px;border-radius:8px">Core</span>'
            if is_core else
            '<span style="background:#0a1020;color:#6b7280;border:1px solid #2a2f3d;font-size:8px;padding:2px 6px;border-radius:8px">Optional</span>'
        )
        rows_html += (
            f'<div style="display:grid;grid-template-columns:1.4fr 2.5fr 90px;gap:8px;'
            f'padding:7px 14px;border-bottom:1px solid #1a1e27;align-items:center">'
            f'<div style="font-family:DM Mono,monospace;font-size:11px;color:#c8f135">{col_name}</div>'
            f'<div style="font-size:11px;color:#6b7280">{unlocks}</div>'
            f'<div>{core_badge}</div>'
            f'</div>'
        )
    st.markdown(card(hdr + rows_html, padding="0", bg="#13161d"), unsafe_allow_html=True)


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

# ── Session state: CSV upload ─────────────────────────────────────────────────
if "csv_df" not in st.session_state:
    st.session_state["csv_df"] = None
if "csv_col_map" not in st.session_state:
    st.session_state["csv_col_map"] = {}

# ── Show upload screen if no CSV loaded yet ───────────────────────────────────
if st.session_state["csv_df"] is None:
    render_upload_screen()
    st.stop()

# ── CSV is loaded — show detected columns summary + reset option ──────────────
df       = st.session_state["csv_df"]
col_map  = st.session_state["csv_col_map"]
features = check_features(col_map)

detected_count = len(col_map)
_det_color = "#22c55e" if detected_count >= 7 else "#f59e0b" if detected_count >= 4 else "#ef4444"
_det_col, _reset_col = st.columns([8, 1])
with _det_col:
    det_pills = "".join(
        f'<span style="background:#052e16;color:#22c55e;border:1px solid #22c55e30;font-size:9px;'
        f'padding:2px 8px;border-radius:8px;margin-right:4px">{c}</span>'
        for c in col_map.keys()
    )
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:2px">'
        f'<span style="font-size:10px;color:{_det_color}">● {detected_count} columns detected</span>'
        f'{det_pills}</div>',
        unsafe_allow_html=True,
    )
with _reset_col:
    if st.button("↩ Reset CSV", key="reset_csv"):
        st.session_state["csv_df"] = None
        st.session_state["csv_col_map"] = {}
        st.rerun()

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Page nav ──────────────────────────────────────────────────────────────────
page_nav = st.radio("Page", ["📊 Dashboard", "🛡 Player Welfare", "🤝 Sponsorship", "🏟 Matchday", "🌍 Fan Acquisition"], horizontal=True, key="page_nav")
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── Use "Arsenal W" as demo context for club-specific pages ───────────────────
selected = "Arsenal W"  # fallback club for pages that need WSL_CLUBS lookups

if page_nav == "🛡 Player Welfare":
    _render_player_welfare(selected)
    st.stop()

# ── Load — CSV-driven ──────────────────────────────────────────────────────────
with st.spinner("Building fan intelligence from your data..."):
    d = build_csv_data_dict(df, col_map)

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

if page_nav == "🤝 Sponsorship":
    _render_sponsorship(selected, d)
    st.stop()
elif page_nav == "🏟 Matchday":
    _render_matchday(selected, d)
    st.stop()
elif page_nav == "🌍 Fan Acquisition":
    _render_fan_acquisition(selected, d)
    st.stop()

# ── Source legend ─────────────────────────────────────────────────────────────
def pill(label, source_type):
    if source_type == "live":
        return f'<span style="background:#052e16;color:#22c55e;border:1px solid #166534;font-size:9px;padding:2px 8px;border-radius:10px;margin-right:5px">⬤ Live · {label}</span>'
    if source_type == "csv":
        return f'<span style="background:#0a1020;color:#3d9cf0;border:1px solid #1e3a5f;font-size:9px;padding:2px 8px;border-radius:10px;margin-right:5px">● Your data · {label}</span>'
    return f'<span style="background:#1c1500;color:#f59e0b;border:1px solid #92400e;font-size:9px;padding:2px 8px;border-radius:10px;margin-right:5px">◯ Modelled · {label}</span>'

_sent_src = sources["sentiment"]  # "csv", "live", or "simulated"
_cont_src = sources["content"]
st.markdown(
    '<span style="font-size:10px;color:#4b5563;margin-right:6px">Sources:</span>'
    + pill("Engagement", _sent_src)
    + pill("Tickets", "csv" if "Tickets_Purchased" in col_map else "modelled")
    + pill("Player data", "csv" if "Favourite_Player" in col_map else "modelled")
    + pill("Predictions", "modelled"),
    unsafe_allow_html=True)
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ── How-to Guide (shown on first visit, dismissed via session state) ───────────
if "guide_dismissed" not in st.session_state:
    st.session_state["guide_dismissed"] = False

if not st.session_state["guide_dismissed"]:
    total_fans_str = f"{len(df):,}"
    st.markdown(f"""
    <div style="background:#0d1117;border:1px solid #c8f13540;border-radius:10px;padding:20px 24px;margin-bottom:4px">
        <div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:#c8f135;margin-bottom:14px;letter-spacing:-.3px">
            ✦ Your fan data is loaded — {total_fans_str} fans · {len(col_map)} columns detected
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px">
            <div>
                <div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">How it works</div>
                <div style="font-size:11px;color:#6b7280;line-height:1.7">
                    FanIntel auto-detected your column names and built the dashboard from your data.
                    Sections marked <span style="color:#22c55e">From your data</span> use your real numbers.
                    Sections marked <span style="color:#f59e0b">Modelled</span> are computed estimates.
                </div>
            </div>
            <div>
                <div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Feature gating</div>
                <div style="font-size:11px;color:#6b7280;line-height:1.7">
                    Modules unlock based on which columns were detected. Player Intelligence requires
                    <span style="color:#c8f135">Favourite_Player</span>. Churn Risk requires
                    <span style="color:#c8f135">Last_Attended</span>. Scroll down to see what's active.
                </div>
            </div>
            <div>
                <div style="font-size:9px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Key metric scales</div>
                <div style="font-size:11px;color:#6b7280;line-height:1.8">
                    <span style="color:#9ca3af">FanIntel Score</span> — 0 to 100 &nbsp;·&nbsp; 70+ = healthy<br>
                    <span style="color:#9ca3af">Engagement Score</span> — 0 to 100 &nbsp;·&nbsp; &gt;65 = strong<br>
                    <span style="color:#9ca3af">Ticket Demand</span> — 0 to 1 &nbsp;·&nbsp; 1.0 = all fans bought<br>
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
    + f'<div style="background:#0a0c10;border-radius:5px;height:6px;overflow:hidden;margin-bottom:6px">'
    + f'<div style="width:{fanIntel_score}%;height:100%;background:{fi_color};border-radius:5px"></div>'
    + '</div>'
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
k1,k3,k4,k5 = st.columns(4)
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
with k3: st.markdown(kpi_html("Ticket Demand", kpis["demand_index"],
    f"{'▲ Strong' if kpis['demand_index']>=.8 else '— Average' if kpis['demand_index']>=.65 else '▼ Below avg'}",
    "#e8eaf0", "#22c55e" if kpis["demand_index"]>=.75 else "#f59e0b",
    sub_delta="0 – 1 scale &nbsp;·&nbsp; 0 = no demand, 1 = sold out"), unsafe_allow_html=True)
with k4: st.markdown(kpi_html("Fan Risk Score", f"{kpis['overall_risk']}/100",
    f"{'🔴 High risk' if kpis['overall_risk']>=60 else '🟡 Medium risk' if kpis['overall_risk']>=35 else '🟢 Low risk'}",
    risk_color, risk_color,
    sub_delta="0 – 100 &nbsp;·&nbsp; lower is better"), unsafe_allow_html=True)
with k5:
    _total_fans = d.get("total_fans", len(df))
    _avg_spend  = ""
    if "Spend" in col_map:
        _sp = pd.to_numeric(df[col_map["Spend"]], errors="coerce")
        _avg_spend = f"£{_sp.mean():.0f} avg spend"
    st.markdown(kpi_html("Fan Database", f"{_total_fans:,}",
        _avg_spend if _avg_spend else f"Detected: {len(col_map)} columns",
        "#e8eaf0", "#6b7280",
        sub_delta="Total fans in uploaded CSV"), unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Fan Risk Engine ───────────────────────────────────────────────────────────
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

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Fan intelligence signals ──────────────────────────────────────────────────
st.markdown('<div style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0;margin-bottom:10px">Fan intelligence signals</div>', unsafe_allow_html=True)
priority_border = {"HIGH":"#ef4444","MED":"#f59e0b","OPT":"#3d9cf0","LOW":"#22c55e"}
priority_bg     = {"HIGH":"#1f0a0a","MED":"#1c1500","OPT":"#0a1020","LOW":"#0a1f0a"}
for sig in signals:
    bc = priority_border.get(sig["priority"],"#2a2f3d")
    bg = priority_bg.get(sig["priority"],"#13161d")
    _sig_src_badge = source_badge(sig.get("source","") == "From your data")

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
            {risk_badge(sig['priority'])}{sig['title']}{_sig_src_badge}
        </div>
        <div style="font-size:11px;color:#6b7280;line-height:1.5;margin-bottom:6px">{sig['desc']}</div>
        <div style="font-size:10px;color:#3d9cf0">→ {sig.get('action','Review data')}</div>
        {ai_block}
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Fan Cohort Breakdown ──────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:8px 0 14px'>", unsafe_allow_html=True)
_cohort_from_data = features.get("fan_cohorts", False)
st.markdown(
    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
    f'<span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0">Fan cohort breakdown · at-risk segments</span>'
    f'{source_badge(_cohort_from_data)}'
    f'</div>',
    unsafe_allow_html=True,
)

if not cohorts:
    feature_gate_placeholder("Fan Cohort Breakdown", ["Age"])
else:
    cohort_cols = st.columns(len(cohorts))
    for i, cohort in enumerate(cohorts):
        r = cohort["risk_score"]
        risk_c = "#ef4444" if r >= 65 else "#f59e0b" if r >= 40 else "#22c55e"
        risk_label = "HIGH RISK" if r >= 65 else "MED RISK" if r >= 40 else "LOW RISK"
        eng = cohort["engagement"]
        # Actionable recommendation with channel/timing/trigger if available
        if cohort.get("channel"):
            channel_html = (
                f'<div style="background:#0a1020;border:1px solid #1e3a5f;border-radius:5px;padding:7px 9px;margin-top:8px">'
                f'<div style="font-size:8px;color:#3d9cf0;letter-spacing:.06em;margin-bottom:4px">RECOMMENDED ACTION</div>'
                f'<div style="font-size:9px;color:#6b7280;line-height:1.5"><span style="color:#9ca3af">Channel:</span> {cohort["channel"]}</div>'
                f'<div style="font-size:9px;color:#6b7280;line-height:1.5"><span style="color:#9ca3af">Timing:</span> {cohort["timing"]}</div>'
                f'<div style="font-size:9px;color:#6b7280;line-height:1.5"><span style="color:#9ca3af">Trigger:</span> {cohort["trigger"]}</div>'
                + (f'<div style="font-size:9px;color:#c8f135;line-height:1.5;margin-top:3px">Offer: {cohort["offer"]}</div>' if cohort.get("offer") else "")
                + '</div>'
            )
        else:
            channel_html = f'<div style="font-size:9px;color:#3d9cf0;line-height:1.4;margin-top:8px">→ {cohort["action"]}</div>'

        data_badge = source_badge(cohort.get("source") == "from_data")
        with cohort_cols[i]:
            st.markdown(f"""
            <div style="background:#13161d;border:1px solid #1f2937;border-top:3px solid {risk_c};border-radius:8px;padding:14px 12px;height:100%">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                    <div style="font-size:11px;color:#e8eaf0;font-weight:500">{cohort['name']}</div>
                    {data_badge}
                </div>
                <div style="font-family:Syne,sans-serif;font-size:26px;font-weight:800;color:{risk_c};line-height:1">{r}</div>
                <div style="font-size:9px;color:{risk_c};margin-bottom:2px;letter-spacing:.05em">{risk_label}</div>
                <div style="font-size:9px;color:#374151;margin-bottom:8px">risk score · 0 – 100</div>
                <div style="background:#0a0c10;border-radius:3px;height:4px;margin-bottom:8px;overflow:hidden">
                    <div style="width:{r}%;height:100%;background:{risk_c};border-radius:3px"></div>
                </div>
                <div style="font-size:9px;color:#6b7280;margin-bottom:4px">{cohort['size_pct']}% of fanbase{' · ' + str(cohort.get('count','')) + ' fans' if cohort.get('count') else ''}</div>
                <div style="font-size:9px;color:#4b5563;margin-bottom:0">Engagement: {eng}%</div>
                {channel_html}
            </div>""", unsafe_allow_html=True)

# ── Feature 1: Attendance Prediction Engine ───────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:16px 0 16px'>", unsafe_allow_html=True)
_att_from_data = features.get("attendance_prediction", False)
st.markdown(
    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
    f'<span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0">Attendance Prediction Engine · per fixture</span>'
    f'{source_badge(_att_from_data)}'
    f'</div>',
    unsafe_allow_html=True,
)

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

# ── Feature 3: Player Sentiment Influence ─────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:20px 0 16px'>", unsafe_allow_html=True)
_player_src = "from_data" if features.get("player_intelligence") else "modelled"
_player_badge_html = source_badge(_player_src == "from_data")
st.markdown(
    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
    f'<span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0">Player Sentiment Intelligence · ranked by marketing value</span>'
    f'{_player_badge_html}'
    f'</div>',
    unsafe_allow_html=True,
)

if not features.get("player_intelligence"):
    feature_gate_placeholder("Player Sentiment Intelligence", ["Favourite_Player"])
elif player_influence:
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
    if features.get("player_intelligence"):
        st.markdown('<div style="color:#4b5563;font-size:11px">No player data computed.</div>', unsafe_allow_html=True)

# ── Feature 4: Sponsor Exposure Score ─────────────────────────────────────────
st.markdown("<hr style='border-color:#1f2937;margin:20px 0 16px'>", unsafe_allow_html=True)
st.markdown(
    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
    f'<span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:#e8eaf0">Sponsor Exposure Score · per fixture</span>'
    f'{source_badge(False)}'
    f'</div>',
    unsafe_allow_html=True,
)

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
_fan_count_footer = d.get("total_fans", len(df))
st.markdown(
    f'<div style="font-size:10px;color:#374151;text-align:center;padding:20px 0 8px;border-top:1px solid #1f2937;margin-top:16px">'
    f'FanIntel WSL · {datetime.now().strftime("%B %Y")} · '
    f'Driven by your data ({_fan_count_footer:,} fans · {len(col_map)} columns) · '
    f'Attendance &amp; sponsor predictions are modelled estimates · Not for redistribution'
    f'</div>',
    unsafe_allow_html=True,
)
