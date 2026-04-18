import os, json, time, random, hashlib
from datetime import datetime, timedelta
from pathlib import Path
import requests
import numpy as np

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 6 * 3600

WSL_CLUBS = {
    "Arsenal W": {
        "search_query": "Arsenal Women FC WSL 2024",
        "reddit_terms": ["Arsenal Women", "Arsenal W", "Vivianne Miedema", "Beth Mead"],
        "color": "#EF0107", "stadium": "Meadow Park", "capacity": 5000,
        "rivals": ["Chelsea W", "Man City W"],
        "form": ["W","W","L","W","D"],
        "avg_attendance_pct": 87,
    },
    "Chelsea W": {
        "search_query": "Chelsea Women FC WSL highlights 2024",
        "reddit_terms": ["Chelsea Women", "Chelsea W", "Sam Kerr", "Harder"],
        "color": "#034694", "stadium": "Kingsmeadow", "capacity": 4850,
        "rivals": ["Arsenal W", "Man City W"],
        "form": ["W","W","W","L","W"],
        "avg_attendance_pct": 91,
    },
    "Man City W": {
        "search_query": "Manchester City Women WSL 2024",
        "reddit_terms": ["Man City Women", "Manchester City W", "MCWFC"],
        "color": "#6CABDD", "stadium": "Joie Stadium", "capacity": 7000,
        "rivals": ["Arsenal W", "Chelsea W"],
        "form": ["L","D","L","W","L"],
        "avg_attendance_pct": 54,
    },
    "Aston Villa W": {
        "search_query": "Aston Villa Women WSL 2024",
        "reddit_terms": ["Aston Villa Women", "Villa W", "Lehmann"],
        "color": "#95BFE5", "stadium": "Villa Park", "capacity": 42682,
        "rivals": ["Birmingham W"],
        "form": ["W","L","W","W","D"],
        "avg_attendance_pct": 74,
    },
    "Brighton W": {
        "search_query": "Brighton Women Hove Albion WSL 2024",
        "reddit_terms": ["Brighton Women", "Brighton W", "Seagulls Women"],
        "color": "#0057B8", "stadium": "Broadfield Stadium", "capacity": 5500,
        "rivals": ["Crystal Palace W"],
        "form": ["D","W","L","W","W"],
        "avg_attendance_pct": 71,
    },
}

FIXTURES = {
    "Arsenal W": [
        {"opponent":"Chelsea W","date":"2025-04-20","home":True,"att_pct":94,"is_rival":True,"days_away":2},
        {"opponent":"Man City W","date":"2025-04-27","home":False,"att_pct":71,"is_rival":True,"days_away":9},
        {"opponent":"Brighton W","date":"2025-05-04","home":True,"att_pct":88,"is_rival":False,"days_away":16},
    ],
    "Chelsea W": [
        {"opponent":"Arsenal W","date":"2025-04-20","home":False,"att_pct":91,"is_rival":True,"days_away":2},
        {"opponent":"Brighton W","date":"2025-04-26","home":True,"att_pct":79,"is_rival":False,"days_away":8},
        {"opponent":"Aston Villa W","date":"2025-05-03","home":False,"att_pct":65,"is_rival":False,"days_away":15},
    ],
    "Man City W": [
        {"opponent":"Arsenal W","date":"2025-04-27","home":True,"att_pct":58,"is_rival":True,"days_away":9},
        {"opponent":"Aston Villa W","date":"2025-05-01","home":False,"att_pct":61,"is_rival":False,"days_away":13},
        {"opponent":"Chelsea W","date":"2025-05-11","home":True,"att_pct":44,"is_rival":True,"days_away":23},
    ],
    "Aston Villa W": [
        {"opponent":"Brighton W","date":"2025-04-19","home":True,"att_pct":82,"is_rival":False,"days_away":1},
        {"opponent":"Man City W","date":"2025-05-01","home":True,"att_pct":76,"is_rival":False,"days_away":13},
        {"opponent":"Chelsea W","date":"2025-05-03","home":False,"att_pct":65,"is_rival":False,"days_away":15},
    ],
    "Brighton W": [
        {"opponent":"Aston Villa W","date":"2025-04-19","home":False,"att_pct":74,"is_rival":False,"days_away":1},
        {"opponent":"Chelsea W","date":"2025-04-26","home":False,"att_pct":68,"is_rival":False,"days_away":8},
        {"opponent":"Arsenal W","date":"2025-05-04","home":False,"att_pct":81,"is_rival":True,"days_away":16},
    ],
}

WSL_LEAGUE_CONTEXT = {
    "Arsenal W":     {"position":2,"pts":45,"gd":28,"last_5_form":["W","W","L","W","D"],"goals_for":48,"goals_against":20},
    "Chelsea W":     {"position":1,"pts":49,"gd":35,"last_5_form":["W","W","W","L","W"],"goals_for":52,"goals_against":17},
    "Man City W":    {"position":6,"pts":28,"gd":-4,"last_5_form":["L","D","L","W","L"],"goals_for":31,"goals_against":35},
    "Aston Villa W": {"position":4,"pts":38,"gd":12,"last_5_form":["W","L","W","W","D"],"goals_for":39,"goals_against":27},
    "Brighton W":    {"position":5,"pts":33,"gd":6, "last_5_form":["D","W","L","W","W"],"goals_for":35,"goals_against":29},
}

def _cache_path(key):
    h = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{h}.json"

def _cache_get(key):
    p = _cache_path(key)
    if p.exists():
        data = json.loads(p.read_text())
        if time.time() - data["ts"] < CACHE_TTL:
            return data["payload"]
    return None

def _cache_set(key, payload):
    _cache_path(key).write_text(json.dumps({"ts": time.time(), "payload": payload}))

def fetch_youtube_videos(club_name, max_results=8):
    cache_key = f"yt_{club_name}_{max_results}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    club = WSL_CLUBS[club_name]
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {"part":"snippet","q":club["search_query"],"type":"video",
              "maxResults":max_results,"order":"viewCount","key":YOUTUBE_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("items", [])
        video_ids = [i["id"]["videoId"] for i in items if i["id"].get("videoId")]
        if not video_ids:
            return _simulated_videos(club_name)
        sr = requests.get("https://www.googleapis.com/youtube/v3/videos",
            params={"part":"statistics,snippet","id":",".join(video_ids),"key":YOUTUBE_API_KEY}, timeout=10)
        sr.raise_for_status()
        videos = []
        for v in sr.json().get("items", []):
            stats = v.get("statistics", {})
            snippet = v.get("snippet", {})
            views = int(stats.get("viewCount", 0))
            if views < 1000:
                continue
            videos.append({
                "title": snippet.get("title", "")[:65],
                "views": views,
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "published": snippet.get("publishedAt", "")[:10],
                "url": f"https://youtube.com/watch?v={v['id']}",
                "source": "live",
            })
        videos.sort(key=lambda x: x["views"], reverse=True)
        if not videos:
            return _simulated_videos(club_name)
        _cache_set(cache_key, videos)
        return videos
    except Exception:
        return _simulated_videos(club_name)

def _simulated_videos(club_name):
    random.seed(hash(club_name) % 9999)
    titles = [
        f"{club_name} — Best Goals This Season | WSL Highlights",
        f"Match Highlights: {club_name} | Women's Super League",
        f"Player of the Month | {club_name} | WSL 2024-25",
        f"Behind the Scenes: {club_name} Training Ground Access",
        f"{club_name} Fan Reactions | Matchday Vlog",
    ]
    videos = []
    for title in titles:
        days_ago = random.randint(2, 30)
        pub_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        videos.append({
            "title": title, "views": random.randint(80000, 850000),
            "likes": random.randint(2000, 18000), "comments": random.randint(200, 2000),
            "published": pub_date, "url": "", "source": "simulated",
        })
    return sorted(videos, key=lambda x: x["views"], reverse=True)

def _simulated_sentiment(club_name):
    random.seed(hash(club_name + "sent2025") % 9999)
    base = {"Arsenal W":74,"Chelsea W":69,"Man City W":58,"Aston Villa W":67,"Brighton W":71}.get(club_name, 65)
    score = base + random.randint(-2, 2)
    pos = random.randint(48, 68)
    neg = random.randint(8, 22)
    return {
        "score": score, "post_count": random.randint(60, 200),
        "positive_pct": pos, "negative_pct": neg, "neutral_pct": 100-pos-neg,
        "source": "simulated",
    }

def get_sentiment_data(club_name):
    cache_key = f"sent_{club_name}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    try:
        import praw
        from textblob import TextBlob
        reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID",""),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET",""),
            user_agent="WSLFanIntel/1.0",
        )
        terms = WSL_CLUBS[club_name]["reddit_terms"]
        posts = []
        for sub in ["WomensSuperLeague","Lionesses","soccer","football"]:
            try:
                for s in reddit.subreddit(sub).new(limit=60):
                    text = f"{s.title} {s.selftext}"
                    if any(t.lower() in text.lower() for t in terms):
                        blob = TextBlob(text)
                        posts.append({"score": blob.sentiment.polarity, "upvotes": s.score})
            except:
                continue
        if len(posts) < 5:
            return _simulated_sentiment(club_name)
        scores = [p["score"] for p in posts]
        avg = np.mean(scores)
        normalized = int(((avg + 1) / 2) * 100)
        normalized = max(35, min(95, normalized))
        pos = int(sum(1 for s in scores if s > 0.05) / len(scores) * 100)
        neg = int(sum(1 for s in scores if s < -0.05) / len(scores) * 100)
        result = {
            "score": normalized, "post_count": len(posts),
            "positive_pct": pos, "negative_pct": neg, "neutral_pct": 100-pos-neg,
            "source": "live",
        }
        _cache_set(cache_key, result)
        return result
    except:
        return _simulated_sentiment(club_name)

def get_sentiment_trend(club_name, days=14):
    cache_key = f"trend_{club_name}_{days}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    random.seed(hash(club_name + "trend2025") % 9999)
    base = {"Arsenal W":68,"Chelsea W":65,"Man City W":54,"Aston Villa W":61,"Brighton W":67}.get(club_name, 63)
    dates = [(datetime.now()-timedelta(days=days-i)).strftime("%b %d") for i in range(days)]
    def wave(offset, vol):
        v, vals = base+offset, []
        for _ in range(days):
            v += random.uniform(-vol, vol)
            vals.append(round(max(30, min(95, v)), 1))
        return vals
    result = {"dates":dates,"twitter":wave(-2,4),"instagram":wave(5,3),"youtube":wave(-6,2.5),"reddit":wave(1,3.5)}
    _cache_set(cache_key, result)
    return result

def compute_fan_risk_score(club_name, sentiment_score, fixtures, form):
    """
    The core engine. Combines sentiment + form + fixture context + urgency.
    Returns per-fixture risk scores and an overall club risk level.
    """
    losses = form.count("L")
    draws  = form.count("D")
    form_score = max(0, 100 - (losses * 20) - (draws * 8))

    sentiment_weight = 0.35
    form_weight      = 0.30
    ticket_weight    = 0.20
    urgency_weight   = 0.15

    fixture_risks = []
    for f in fixtures:
        rival_boost   = 25 if f["is_rival"] else 0
        urgency_boost = max(0, 20 - f["days_away"])
        base_ticket   = f["att_pct"]
        adjusted_ticket = min(100, base_ticket + rival_boost)

        raw = (
            sentiment_score  * sentiment_weight +
            form_score       * form_weight +
            adjusted_ticket  * ticket_weight +
            urgency_boost    * urgency_weight
        )
        risk = 100 - raw
        risk = max(5, min(95, risk))

        if risk >= 65:
            level = "HIGH"
        elif risk >= 40:
            level = "MED"
        else:
            level = "LOW"

        fixture_risks.append({
            **f,
            "risk_score": round(risk, 1),
            "risk_level": level,
            "rival_boost": rival_boost,
            "form_score": round(form_score, 1),
            "adjusted_ticket": adjusted_ticket,
        })

    overall = round(np.mean([r["risk_score"] for r in fixture_risks]), 1)
    return {"fixture_risks": fixture_risks, "overall_risk": overall}

def generate_signals(club_name, sentiment, risk_data, content_views, league):
    signals = []
    form = WSL_CLUBS[club_name]["form"]
    losses = form.count("L")
    fixture_risks = risk_data["fixture_risks"]
    high_risk_fixtures = [f for f in fixture_risks if f["risk_level"] == "HIGH"]
    rival_fixtures = [f for f in fixture_risks if f["is_rival"]]

    if losses >= 3:
        signals.append({
            "priority":"HIGH",
            "title": f"Form crisis — {losses} losses in last 5",
            "desc": f"Fan sentiment has dropped {abs(sentiment['score']-75)} pts alongside the run. Win-back campaign needed before next home game.",
            "source":"Form + Sentiment","action":"Email lapsed buyers with loyalty discount",
        })

    if high_risk_fixtures:
        f = high_risk_fixtures[0]
        signals.append({
            "priority":"HIGH",
            "title": f"At-risk fixture: vs {f['opponent']} ({f['date']})",
            "desc": f"Fan Risk Score {f['risk_score']}/100. Sentiment down, form poor, {f['days_away']} days to act.",
            "source":"Fan Risk Engine","action":"Launch targeted ticket campaign now",
        })

    if rival_fixtures:
        f = rival_fixtures[0]
        signals.append({
            "priority":"MED" if f["att_pct"] > 80 else "HIGH",
            "title": f"Derby vs {f['opponent']} — demand {'strong' if f['att_pct']>80 else 'below expectations'}",
            "desc": f"{'Rival fixture driving demand despite poor form — capitalise with hospitality upsell.' if f['att_pct']>80 else 'Derby underperforming. Fan disengagement risk is real.'}",
            "source":"Fixture Intelligence","action":"Push premium matchday packages",
        })

    if sentiment["score"] > 70 and losses < 2:
        signals.append({
            "priority":"MED",
            "title":"Fan energy high — membership window open",
            "desc":"Positive sentiment + good form = best conversion window for season ticket renewals.",
            "source":"Sentiment + Form","action":"Launch early renewal campaign",
        })

    if club_name == "Aston Villa W":
        signals.append({
            "priority":"HIGH",
            "title":"Star player effect — content revenue untapped",
            "desc":"Top player content drives 6x club average reach but no commercial link in posts. Sponsorship + merch opportunity.",
            "source":"Content Analysis","action":"Add affiliate/merch links to top 5 videos",
        })

    if club_name == "Man City W":
        signals.append({
            "priority":"MED",
            "title":"Joie Stadium severely underutilised",
            "desc":"7,000 capacity but averaging 54% — 3,220 empty seats per game. Community outreach + school programs could fill 15%.",
            "source":"Attendance Intelligence","action":"Partner with local schools for junior fan days",
        })

    signals.append({
        "priority":"OPT",
        "title":"Pre-match content window underused",
        "desc":"Sentiment peaks 48h before kickoff but posting drops. Schedule 2 posts in this window.",
        "source":"Content Cadence","action":"Automate pre-match content scheduler",
    })

    return signals[:4]

def get_content_engagement(club_name):
    videos = fetch_youtube_videos(club_name, max_results=6)
    total_views = sum(v["views"] for v in videos)
    total_likes = sum(v["likes"] for v in videos)
    eng_rate = round(total_likes / total_views * 100, 2) if total_views > 0 else 0
    if total_views >= 1_000_000:
        reach_label = f"{total_views/1_000_000:.1f}M"
    elif total_views >= 1000:
        reach_label = f"{total_views//1000}K"
    else:
        reach_label = str(total_views)
    return {
        "total_views": total_views, "reach_label": reach_label,
        "engagement_rate": eng_rate, "top_videos": videos[:5],
        "source": videos[0]["source"] if videos else "simulated",
    }

def get_ticket_demand(club_name):
    fixtures = FIXTURES.get(club_name, [])
    demand_index = round(np.mean([f["att_pct"] for f in fixtures]) / 100, 2) if fixtures else 0.5
    processed = []
    for f in fixtures:
        pct = f["att_pct"]
        velocity = "Selling fast" if pct >= 85 else "Rising" if pct >= 70 else "Steady" if pct >= 55 else "Slow"
        processed.append({**f, "velocity": velocity})
    return {"demand_index": demand_index, "fixtures": processed}

def get_full_club_data(club_name):
    sentiment  = get_sentiment_data(club_name)
    content    = get_content_engagement(club_name)
    tickets    = get_ticket_demand(club_name)
    trend      = get_sentiment_trend(club_name)
    league     = WSL_LEAGUE_CONTEXT.get(club_name, {})
    form       = WSL_CLUBS[club_name]["form"]
    risk_data  = compute_fan_risk_score(club_name, sentiment["score"], tickets["fixtures"], form)
    signals    = generate_signals(club_name, sentiment, risk_data, content["total_views"], league)
    risk_alerts = sum(1 for s in signals if s["priority"] == "HIGH")
    return {
        "club": club_name,
        "sentiment": sentiment,
        "content": content,
        "tickets": tickets,
        "trend": trend,
        "signals": signals,
        "risk_data": risk_data,
        "league": league,
        "form": form,
        "kpis": {
            "sentiment_score": sentiment["score"],
            "content_reach": content["reach_label"],
            "demand_index": tickets["demand_index"],
            "risk_alerts": risk_alerts,
            "overall_risk": risk_data["overall_risk"],
        },
        "data_sources": {
            "sentiment": sentiment.get("source","simulated"),
            "content": content.get("source","simulated"),
        }
    }
