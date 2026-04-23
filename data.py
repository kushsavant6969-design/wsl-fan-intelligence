import os, json, time, random, hashlib
from datetime import datetime, timedelta
from pathlib import Path
import requests
import numpy as np

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 6 * 3600

WSL_CLUBS = {
    "Arsenal W": {
        "search_query": "Arsenal Women FC WSL 2024",
        "reddit_terms": ["Arsenal Women", "Arsenal W", "Vivianne Miedema", "Beth Mead"],
        "color": "#EF0107", "stadium": "Meadow Park", "capacity": 5000,
        "rivals": ["Chelsea W", "Man City W"],
        "form":      ["W",  "W",  "L",  "W",  "D"  ],
        "form_comp": ["UCL","WSL","WSL","FAC","WSL"],
        "avg_attendance_pct": 87,
    },
    "Chelsea W": {
        "search_query": "Chelsea Women FC WSL highlights 2024",
        "reddit_terms": ["Chelsea Women", "Chelsea W", "Sam Kerr", "Harder"],
        "color": "#034694", "stadium": "Kingsmeadow", "capacity": 4850,
        "rivals": ["Arsenal W", "Man City W"],
        "form":      ["W",  "W",  "W",  "L",  "W"  ],
        "form_comp": ["WSL","UCL","WSL","UCL","WSL"],
        "avg_attendance_pct": 91,
    },
    "Man City W": {
        "search_query": "Manchester City Women WSL 2024",
        "reddit_terms": ["Man City Women", "Manchester City W", "MCWFC"],
        "color": "#6CABDD", "stadium": "Joie Stadium", "capacity": 7000,
        "rivals": ["Arsenal W", "Chelsea W"],
        "form":      ["L",  "D",  "L",  "W",  "L"  ],
        "form_comp": ["WSL","WSL","FAC","WSL","WSL"],
        "avg_attendance_pct": 54,
    },
    "Aston Villa W": {
        "search_query": "Aston Villa Women WSL 2024",
        "reddit_terms": ["Aston Villa Women", "Villa W", "Lehmann"],
        "color": "#95BFE5", "stadium": "Villa Park", "capacity": 42682,
        "rivals": ["Birmingham W"],
        "form":      ["W",  "L",  "W",  "W",  "D"  ],
        "form_comp": ["WSL","FAC","WSL","WSL","WSL"],
        "avg_attendance_pct": 74,
    },
    "Brighton W": {
        "search_query": "Brighton Women Hove Albion WSL 2024",
        "reddit_terms": ["Brighton Women", "Brighton W", "Seagulls Women"],
        "color": "#0057B8", "stadium": "Broadfield Stadium", "capacity": 5500,
        "rivals": ["Crystal Palace W"],
        "form":      ["D",  "W",  "L",  "W",  "W"  ],
        "form_comp": ["WSL","FAC","WSL","WSL","WSL"],
        "avg_attendance_pct": 71,
    },
    "WSL Overall": {
        "search_query": "Women's Super League WSL highlights 2024",
        "reddit_terms": ["WSL", "Women's Super League", "FAWSL"],
        "color": "#c8f135", "stadium": "Various", "capacity": 13006,
        "rivals": [],
        "form":      ["W",  "D",  "W",  "L",  "W"  ],
        "form_comp": ["WSL","WSL","UCL","FAC","WSL"],
        "avg_attendance_pct": 75,
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
    "WSL Overall": [
        {"opponent":"Arsenal W vs Chelsea W","date":"2025-04-20","home":True,"att_pct":94,"is_rival":True,"days_away":2},
        {"opponent":"Brighton W vs Aston Villa W","date":"2025-04-19","home":True,"att_pct":74,"is_rival":False,"days_away":1},
        {"opponent":"Man City W vs Aston Villa W","date":"2025-05-01","home":True,"att_pct":61,"is_rival":False,"days_away":13},
    ],
}

WSL_LEAGUE_CONTEXT = {
    "Arsenal W":     {"position":2,"pts":45,"gd":28,"last_5_form":["W","W","L","W","D"],"goals_for":48,"goals_against":20},
    "Chelsea W":     {"position":1,"pts":49,"gd":35,"last_5_form":["W","W","W","L","W"],"goals_for":52,"goals_against":17},
    "Man City W":    {"position":6,"pts":28,"gd":-4,"last_5_form":["L","D","L","W","L"],"goals_for":31,"goals_against":35},
    "Aston Villa W": {"position":4,"pts":38,"gd":12,"last_5_form":["W","L","W","W","D"],"goals_for":39,"goals_against":27},
    "Brighton W":    {"position":5,"pts":33,"gd":6, "last_5_form":["D","W","L","W","W"],"goals_for":35,"goals_against":29},
}

# ── Player sentiment influence data (simulated) ────────────────────────────────
PLAYER_DATA = {
    "Arsenal W": [
        {"name": "Vivianne Miedema", "position": "FW", "sentiment_lift": 9.1, "engagement_mult": 4.1, "merch_index": 95, "marketing_value": 94},
        {"name": "Beth Mead",        "position": "FW", "sentiment_lift": 8.4, "engagement_mult": 3.2, "merch_index": 91, "marketing_value": 88},
        {"name": "Kim Little",       "position": "MF", "sentiment_lift": 6.2, "engagement_mult": 2.4, "merch_index": 72, "marketing_value": 70},
        {"name": "Lotte Wubben-Moy", "position": "DF", "sentiment_lift": 5.8, "engagement_mult": 2.1, "merch_index": 68, "marketing_value": 65},
        {"name": "Manuela Zinsberger","position":"GK", "sentiment_lift": 4.3, "engagement_mult": 1.8, "merch_index": 55, "marketing_value": 52},
    ],
    "Chelsea W": [
        {"name": "Sam Kerr",         "position": "FW", "sentiment_lift": 9.6, "engagement_mult": 4.8, "merch_index": 97, "marketing_value": 96},
        {"name": "Erin Cuthbert",    "position": "MF", "sentiment_lift": 7.2, "engagement_mult": 2.9, "merch_index": 78, "marketing_value": 75},
        {"name": "Millie Bright",    "position": "DF", "sentiment_lift": 6.8, "engagement_mult": 2.6, "merch_index": 74, "marketing_value": 72},
        {"name": "Niamh Charles",    "position": "DF", "sentiment_lift": 5.3, "engagement_mult": 2.2, "merch_index": 63, "marketing_value": 60},
        {"name": "Ann-Katrin Berger","position": "GK", "sentiment_lift": 4.1, "engagement_mult": 1.7, "merch_index": 52, "marketing_value": 50},
    ],
    "Man City W": [
        {"name": "Chloe Kelly",      "position": "FW", "sentiment_lift": 8.9, "engagement_mult": 3.9, "merch_index": 88, "marketing_value": 86},
        {"name": "Lauren Hemp",      "position": "FW", "sentiment_lift": 8.2, "engagement_mult": 3.5, "merch_index": 85, "marketing_value": 82},
        {"name": "Mary Fowler",      "position": "MF", "sentiment_lift": 7.5, "engagement_mult": 3.0, "merch_index": 80, "marketing_value": 77},
        {"name": "Alex Greenwood",   "position": "DF", "sentiment_lift": 6.4, "engagement_mult": 2.5, "merch_index": 70, "marketing_value": 68},
        {"name": "Khiara Keating",   "position": "GK", "sentiment_lift": 5.1, "engagement_mult": 2.0, "merch_index": 58, "marketing_value": 55},
    ],
    "Aston Villa W": [
        {"name": "Rachel Daly",          "position": "FW", "sentiment_lift": 8.0, "engagement_mult": 3.3, "merch_index": 83, "marketing_value": 80},
        {"name": "Daphne van Domselaar", "position": "GK", "sentiment_lift": 7.1, "engagement_mult": 2.8, "merch_index": 76, "marketing_value": 74},
        {"name": "Abbi Grant",           "position": "FW", "sentiment_lift": 6.8, "engagement_mult": 2.7, "merch_index": 73, "marketing_value": 70},
        {"name": "Kirsty Hanson",        "position": "MF", "sentiment_lift": 6.0, "engagement_mult": 2.3, "merch_index": 65, "marketing_value": 62},
        {"name": "Anita Asante",         "position": "DF", "sentiment_lift": 5.5, "engagement_mult": 2.0, "merch_index": 60, "marketing_value": 58},
    ],
    "Brighton W": [
        {"name": "Elisabeth Terland",  "position": "FW", "sentiment_lift": 7.8, "engagement_mult": 3.2, "merch_index": 81, "marketing_value": 78},
        {"name": "Vicky Losada",       "position": "MF", "sentiment_lift": 7.0, "engagement_mult": 2.8, "merch_index": 74, "marketing_value": 71},
        {"name": "Inessa Kaagman",     "position": "MF", "sentiment_lift": 6.3, "engagement_mult": 2.4, "merch_index": 67, "marketing_value": 64},
        {"name": "Maria Thorisdottir", "position": "DF", "sentiment_lift": 5.2, "engagement_mult": 2.0, "merch_index": 58, "marketing_value": 56},
        {"name": "Sophie Baggaley",    "position": "GK", "sentiment_lift": 4.5, "engagement_mult": 1.9, "merch_index": 53, "marketing_value": 50},
    ],
    "WSL Overall": [],
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
    base = {"Arsenal W":74,"Chelsea W":69,"Man City W":58,"Aston Villa W":67,"Brighton W":71,"WSL Overall":68}.get(club_name, 65)
    score = base + random.randint(-2, 2)
    pos = random.randint(48, 68)
    neg = random.randint(8, 22)
    # Simulated 30-day-ago score (deterministic per club)
    seed_30d = hash(club_name + "sent30d2025") % 9999
    rng = random.Random(seed_30d)
    delta_30d = rng.randint(-9, 7)
    score_30d_ago = max(35, min(95, score - delta_30d))
    return {
        "score": score, "post_count": random.randint(60, 200),
        "positive_pct": pos, "negative_pct": neg, "neutral_pct": 100-pos-neg,
        "score_30d_ago": score_30d_ago,
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
        random.seed(hash(club_name + "sent30d2025") % 9999)
        score_30d_ago = max(35, min(95, normalized + random.randint(-9, 7)))
        result = {
            "score": normalized, "post_count": len(posts),
            "positive_pct": pos, "negative_pct": neg, "neutral_pct": 100-pos-neg,
            "score_30d_ago": score_30d_ago,
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
    base = {"Arsenal W":68,"Chelsea W":65,"Man City W":54,"Aston Villa W":61,"Brighton W":67,"WSL Overall":63}.get(club_name, 63)
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

def get_fan_cohorts(club_name):
    rng = random.Random(hash(club_name + "cohorts2025") % 99999)
    base_sent = {"Arsenal W":74,"Chelsea W":69,"Man City W":58,"Aston Villa W":67,"Brighton W":71,"WSL Overall":68}.get(club_name, 65)
    form = WSL_CLUBS.get(club_name, {}).get("form", [])
    losses = form.count("L") if form else 1

    def risk(base, loss_mult, spread=5):
        return min(95, max(10, base - base_sent * 0.3 + losses * loss_mult + rng.randint(-spread, spread)))

    return [
        {
            "name": "18–24 Casual",
            "size_pct": rng.randint(18, 26),
            "risk_score": int(risk(72, 9)),
            "engagement": rng.randint(38, 68),
            "action": "TikTok + Instagram push · £5 off first ticket",
        },
        {
            "name": "25–34 Regular",
            "size_pct": rng.randint(24, 32),
            "risk_score": int(risk(52, 6)),
            "engagement": rng.randint(55, 80),
            "action": "Early-bird season ticket offer",
        },
        {
            "name": "35–49 Loyalist",
            "size_pct": rng.randint(20, 28),
            "risk_score": int(risk(38, 4)),
            "engagement": rng.randint(68, 90),
            "action": "Renewal reminder + hospitality upgrade",
        },
        {
            "name": "50+ Veteran",
            "size_pct": rng.randint(12, 20),
            "risk_score": int(risk(34, 5)),
            "engagement": rng.randint(62, 85),
            "action": "Loyalty recognition programme",
        },
        {
            "name": "Lapsed Buyers",
            "size_pct": rng.randint(8, 16),
            "risk_score": min(95, int(70 + losses * 5 + rng.randint(0, 10))),
            "engagement": rng.randint(12, 32),
            "action": "Win-back email: 20% discount + personalised message",
        },
        {
            "name": "First-Timers",
            "size_pct": rng.randint(4, 10),
            "risk_score": int(risk(58, 3, 10)),
            "engagement": rng.randint(32, 60),
            "action": "Welcome series + buddy ticket offer",
        },
    ]


# ── Feature 1: Attendance Prediction Engine ───────────────────────────────────
def get_attendance_predictions(club_name):
    """Predict stadium fill rate per fixture. Simulated model."""
    fixtures = FIXTURES.get(club_name, [])
    rng = random.Random(hash(club_name + "attpred2025") % 99999)
    sent = _simulated_sentiment(club_name)
    form = WSL_CLUBS.get(club_name, {}).get("form", [])
    avg_hist = WSL_CLUBS.get(club_name, {}).get("avg_attendance_pct", 70)
    losses = form.count("L")

    predictions = []
    for f in fixtures:
        sent_adj   = (sent["score"] - 60) * 0.15
        derby_bonus = 10 if f["is_rival"] else 0
        form_penalty = losses * 3.5
        days_adj   = max(0, (20 - f["days_away"]) / 20) * 4
        predicted  = avg_hist + sent_adj + derby_bonus - form_penalty + days_adj + rng.uniform(-2, 2)
        predicted  = max(15, min(100, predicted))
        conf       = rng.uniform(4, 8)
        predictions.append({
            **f,
            "predicted_pct": round(predicted, 1),
            "confidence_low": round(max(10, predicted - conf), 1),
            "confidence_high": round(min(100, predicted + conf), 1),
            "at_risk": predicted < 70,
            "drivers": {
                "historical": avg_hist,
                "sentiment_adj": round(sent_adj, 1),
                "derby_bonus": derby_bonus,
                "form_penalty": round(-form_penalty, 1),
            },
        })
    return predictions


# ── Feature 2: Fan Churn Risk Score ───────────────────────────────────────────
def get_churn_risk_scores(club_name):
    """Per-cohort churn probability with retention action. Simulated model."""
    rng = random.Random(hash(club_name + "churn2025") % 99999)
    sent = _simulated_sentiment(club_name)
    form = WSL_CLUBS.get(club_name, {}).get("form", [])
    losses = form.count("L")

    COHORT_PROFILES = [
        {"name": "18–24 Casual",   "base_churn": 38, "sent_sens": 0.40, "form_sens": 8,
         "retention": "TikTok-first content series + £5 first-ticket discount code"},
        {"name": "25–34 Regular",  "base_churn": 22, "sent_sens": 0.25, "form_sens": 5,
         "retention": "Early-bird season ticket offer + priority seat selection window"},
        {"name": "35–49 Loyalist", "base_churn": 11, "sent_sens": 0.15, "form_sens": 3,
         "retention": "Auto-renewal prompt + complimentary hospitality upgrade voucher"},
        {"name": "50+ Veteran",    "base_churn":  8, "sent_sens": 0.10, "form_sens": 2,
         "retention": "Legacy membership recognition + personalised captain's letter"},
        {"name": "Lapsed Buyers",  "base_churn": 72, "sent_sens": 0.60, "form_sens": 12,
         "retention": "Win-back email series: 30% off + personalised 'what you missed' reel"},
        {"name": "First-Timers",   "base_churn": 45, "sent_sens": 0.50, "form_sens": 9,
         "retention": "Guided matchday experience + buddy ticket for next home game"},
    ]

    result = []
    for c in COHORT_PROFILES:
        sent_delta = max(0, (65 - sent["score"])) * c["sent_sens"]
        form_delta = losses * c["form_sens"]
        churn = c["base_churn"] + sent_delta + form_delta + rng.uniform(-2, 2)
        churn = round(max(3, min(95, churn)), 1)
        result.append({
            "name": c["name"],
            "churn_pct": churn,
            "retention_action": c["retention"],
            "risk_level": "HIGH" if churn >= 55 else "MED" if churn >= 28 else "LOW",
        })
    return result


# ── Feature 3: Player Sentiment Influence ─────────────────────────────────────
def get_player_sentiment_influence(club_name):
    """5 key players per club ranked by marketing/sentiment value. Simulated data."""
    if club_name == "WSL Overall":
        players = []
        for club in [c for c in PLAYER_DATA if c != "WSL Overall" and PLAYER_DATA[c]]:
            top = max(PLAYER_DATA[club], key=lambda p: p["marketing_value"])
            players.append({**top, "club": club})
        return sorted(players, key=lambda p: p["marketing_value"], reverse=True)
    players = PLAYER_DATA.get(club_name, [])
    return sorted([{**p, "club": club_name} for p in players], key=lambda p: p["marketing_value"], reverse=True)


# ── Feature 4: Sponsor Exposure Score ─────────────────────────────────────────
def get_sponsor_exposure_scores(club_name):
    """Per-fixture sponsor visibility value index (0–100). Simulated model."""
    fixtures = FIXTURES.get(club_name, [])
    rng = random.Random(hash(club_name + "sponsor2025") % 99999)
    sent = _simulated_sentiment(club_name)
    content = get_content_engagement(club_name)
    league_avg = 57

    scores = []
    for f in fixtures:
        content_score  = min(100, content["engagement_rate"] * 8 + rng.uniform(10, 30))
        sentiment_score = sent["score"]
        derby_mult     = 1.45 if f["is_rival"] else 1.0
        broadcast      = rng.uniform(65, 92) if f["is_rival"] else rng.uniform(28, 65)
        raw = (content_score * 0.30 + sentiment_score * 0.25 + broadcast * 0.28 + f["att_pct"] * 0.17)
        idx = round(min(100, max(10, raw * derby_mult)), 1)
        scores.append({
            **f,
            "sponsor_index": idx,
            "vs_benchmark": round(idx - league_avg, 1),
            "broadcast_reach": round(broadcast, 1),
            "is_premium": idx >= 75,
        })
    return {"fixtures": scores, "league_avg": league_avg}

def get_claude_recommendation(club_name, signal_title, signal_desc):
    if not ANTHROPIC_API_KEY:
        return None
    cache_key = f"claude_{hashlib.md5((club_name + signal_title).encode()).hexdigest()}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = (
            f"You are a sports marketing strategist for WSL (Women's Super League) clubs.\n\n"
            f"Club: {club_name}\n"
            f"HIGH-priority signal: {signal_title}\n"
            f"Context: {signal_desc}\n\n"
            f"Generate a specific, actionable fan engagement recommendation. Be concise and concrete.\n\n"
            f"Respond in exactly this format (4 lines):\n"
            f"TARGET: [specific fan segment]\n"
            f"MESSAGE: [the key message or offer — 1 sentence]\n"
            f"TIMING: [when to execute — be specific]\n"
            f"CHANNEL: [which channel(s) to use]"
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.content[0].text.strip()
        _cache_set(cache_key, result)
        return result
    except Exception:
        return None

def compute_fan_risk_score(club_name, sentiment_score, fixtures, form):
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

    overall = round(np.mean([r["risk_score"] for r in fixture_risks]), 1) if fixture_risks else 50.0
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

def generate_wsl_overall_signals(club_sentiments):
    sorted_clubs = sorted(club_sentiments, key=lambda x: x[1])
    lowest, highest = sorted_clubs[0], sorted_clubs[-1]
    return [
        {
            "priority":"HIGH",
            "title": f"Sentiment gap: {highest[0]} ({highest[1]}) vs {lowest[0]} ({lowest[1]})",
            "desc": f"{highest[0]} leads league sentiment at {highest[1]}/100; {lowest[0]} trails at {lowest[1]}/100 — {highest[1]-lowest[1]}pt gap highlights uneven fan health.",
            "source":"League Intelligence","action":"Target low-sentiment clubs with cross-promotion",
        },
        {
            "priority":"HIGH",
            "title":"League-wide attendance below 85% target",
            "desc":"Average capacity utilisation across WSL clubs is 75.4%. Aston Villa's 42k capacity skews the aggregate — targeted pricing review needed.",
            "source":"Attendance Intelligence","action":"Review dynamic pricing at underperforming venues",
        },
        {
            "priority":"MED",
            "title":"Derby weekend — peak engagement window",
            "desc":"Arsenal W vs Chelsea W (Apr 20) is the highest-demand fixture of the run-in. League-wide content opportunity to grow new audiences.",
            "source":"Fixture Intelligence","action":"League-wide social campaign around the derby",
        },
        {
            "priority":"OPT",
            "title":"WSL content reach concentrated in top 2 clubs",
            "desc":"Arsenal W and Chelsea W account for ~65% of total WSL YouTube views. Mid-table clubs underrepresented in league narrative.",
            "source":"Content Analysis","action":"Cross-promote mid-table clubs via league channel",
        },
    ]

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
    if club_name == "WSL Overall":
        return _get_wsl_overall_data()

    sentiment  = get_sentiment_data(club_name)
    content    = get_content_engagement(club_name)
    tickets    = get_ticket_demand(club_name)
    trend      = get_sentiment_trend(club_name)
    league     = WSL_LEAGUE_CONTEXT.get(club_name, {})
    form       = WSL_CLUBS[club_name]["form"]
    form_comp  = WSL_CLUBS[club_name].get("form_comp", ["WSL"] * len(form))
    risk_data  = compute_fan_risk_score(club_name, sentiment["score"], tickets["fixtures"], form)
    signals    = generate_signals(club_name, sentiment, risk_data, content["total_views"], league)
    cohorts    = get_fan_cohorts(club_name)
    risk_alerts = sum(1 for s in signals if s["priority"] == "HIGH")
    attendance_predictions = get_attendance_predictions(club_name)
    churn_risks    = get_churn_risk_scores(club_name)
    player_influence = get_player_sentiment_influence(club_name)
    sponsor_exposure = get_sponsor_exposure_scores(club_name)
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
        "form_comp": form_comp,
        "cohorts": cohorts,
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
        },
        "attendance_predictions": attendance_predictions,
        "churn_risks": churn_risks,
        "player_influence": player_influence,
        "sponsor_exposure": sponsor_exposure,
    }

def _get_wsl_overall_data():
    real_clubs = [c for c in WSL_CLUBS if c != "WSL Overall"]

    # Aggregate sentiment
    sentiments = [_simulated_sentiment(c) for c in real_clubs]
    avg_score = int(np.mean([s["score"] for s in sentiments]))
    avg_pos   = int(np.mean([s["positive_pct"] for s in sentiments]))
    avg_neg   = int(np.mean([s["negative_pct"] for s in sentiments]))
    rng_30d   = random.Random(hash("WSL Overall" + "sent30d2025") % 99999)
    score_30d = max(35, min(95, avg_score + rng_30d.randint(-6, 6)))
    sentiment = {
        "score": avg_score,
        "post_count": sum(s["post_count"] for s in sentiments),
        "positive_pct": avg_pos,
        "negative_pct": avg_neg,
        "neutral_pct": 100 - avg_pos - avg_neg,
        "score_30d_ago": score_30d,
        "source": "simulated",
    }

    # Aggregate content
    all_videos = []
    total_views = 0
    for c in real_clubs:
        ce = get_content_engagement(c)
        total_views += ce["total_views"]
        all_videos.extend(ce["top_videos"][:2])
    all_videos.sort(key=lambda x: x["views"], reverse=True)
    reach_label = f"{total_views/1_000_000:.1f}M" if total_views >= 1_000_000 else f"{total_views//1000}K"
    total_likes = sum(v["likes"] for v in all_videos)
    content = {
        "total_views": total_views,
        "reach_label": reach_label,
        "engagement_rate": round(total_likes / total_views * 100, 2) if total_views else 0,
        "top_videos": all_videos[:5],
        "source": "simulated",
    }

    # Fixtures
    tickets = get_ticket_demand("WSL Overall")

    # Trend: average across clubs
    trends = [get_sentiment_trend(c) for c in real_clubs]
    dates = trends[0]["dates"]
    n = len(dates)
    avg_trend = {"dates": dates}
    for ch in ["twitter","instagram","youtube","reddit"]:
        avg_trend[ch] = [round(np.mean([t[ch][i] for t in trends]), 1) for i in range(n)]

    form      = WSL_CLUBS["WSL Overall"]["form"]
    form_comp = WSL_CLUBS["WSL Overall"].get("form_comp", ["WSL"] * len(form))
    risk_data = compute_fan_risk_score("WSL Overall", avg_score, tickets["fixtures"], form)
    signals = generate_wsl_overall_signals([(real_clubs[i], sentiments[i]["score"]) for i in range(len(real_clubs))])
    cohorts = get_fan_cohorts("WSL Overall")
    risk_alerts = sum(1 for s in signals if s["priority"] == "HIGH")

    attendance_predictions = get_attendance_predictions("WSL Overall")
    churn_risks    = get_churn_risk_scores("WSL Overall")
    player_influence = get_player_sentiment_influence("WSL Overall")
    sponsor_exposure = get_sponsor_exposure_scores("WSL Overall")
    return {
        "club": "WSL Overall",
        "sentiment": sentiment,
        "content": content,
        "tickets": tickets,
        "trend": avg_trend,
        "signals": signals,
        "risk_data": risk_data,
        "league": {"position":"—","pts":"—","gd":"—"},
        "form": form,
        "form_comp": form_comp,
        "cohorts": cohorts,
        "kpis": {
            "sentiment_score": avg_score,
            "content_reach": reach_label,
            "demand_index": tickets["demand_index"],
            "risk_alerts": risk_alerts,
            "overall_risk": risk_data["overall_risk"],
        },
        "data_sources": {"sentiment":"simulated","content":"simulated"},
        "attendance_predictions": attendance_predictions,
        "churn_risks": churn_risks,
        "player_influence": player_influence,
        "sponsor_exposure": sponsor_exposure,
    }
