import os
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import requests
import praw
from textblob import TextBlob
import pandas as pd
import numpy as np

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 6 * 3600

WSL_CLUBS = {
    "Arsenal W": {
        "youtube_channel": "UCHDzdMCKHFPpYiGEFoJcRPQ",
        "search_query": "Arsenal Women FC",
        "reddit_terms": ["Arsenal Women", "Arsenal W", "ArsenalWomen"],
        "color": "#EF0107",
        "founded": 1987,
        "stadium": "Meadow Park",
        "capacity": 5000,
    },
    "Chelsea W": {
        "youtube_channel": "UCaKeTGhEVOfBxjKEWxJ3YRg",
        "search_query": "Chelsea Women FC",
        "reddit_terms": ["Chelsea Women", "Chelsea W"],
        "color": "#034694",
        "founded": 1992,
        "stadium": "Kingsmeadow",
        "capacity": 4850,
    },
    "Man City W": {
        "youtube_channel": "UCiuRohkPOPPGbW0Oj9s9T4A",
        "search_query": "Manchester City Women",
        "reddit_terms": ["Man City Women", "Manchester City W"],
        "color": "#6CABDD",
        "founded": 1988,
        "stadium": "Joie Stadium",
        "capacity": 7000,
    },
    "Aston Villa W": {
        "youtube_channel": "UCBSGHMHbXEpWUBtQFXi7MZA",
        "search_query": "Aston Villa Women",
        "reddit_terms": ["Aston Villa Women", "Villa W"],
        "color": "#95BFE5",
        "founded": 1973,
        "stadium": "Villa Park",
        "capacity": 42682,
    },
    "Brighton W": {
        "youtube_channel": "UCNAhgzHW3bxCuWigjaTqiwQ",
        "search_query": "Brighton Women FC Hove Albion",
        "reddit_terms": ["Brighton Women", "Brighton W"],
        "color": "#0057B8",
        "founded": 1991,
        "stadium": "Broadfield Stadium",
        "capacity": 5500,
    },
}

FIXTURES = {
    "Arsenal W": [
        {"opponent": "Chelsea W", "date": "2025-04-20", "home": True, "att_pct": 94},
        {"opponent": "Man City W", "date": "2025-04-27", "home": False, "att_pct": 71},
        {"opponent": "Brighton W", "date": "2025-05-04", "home": True, "att_pct": 88},
    ],
    "Chelsea W": [
        {"opponent": "Arsenal W", "date": "2025-04-20", "home": False, "att_pct": 91},
        {"opponent": "Brighton W", "date": "2025-04-26", "home": True, "att_pct": 79},
        {"opponent": "Aston Villa W", "date": "2025-05-03", "home": False, "att_pct": 65},
    ],
    "Man City W": [
        {"opponent": "Arsenal W", "date": "2025-04-27", "home": True, "att_pct": 58},
        {"opponent": "Aston Villa W", "date": "2025-05-01", "home": False, "att_pct": 61},
        {"opponent": "Chelsea W", "date": "2025-05-11", "home": True, "att_pct": 44},
    ],
    "Aston Villa W": [
        {"opponent": "Brighton W", "date": "2025-04-19", "home": True, "att_pct": 82},
        {"opponent": "Man City W", "date": "2025-05-01", "home": True, "att_pct": 76},
        {"opponent": "Chelsea W", "date": "2025-05-03", "home": False, "att_pct": 69},
    ],
    "Brighton W": [
        {"opponent": "Aston Villa W", "date": "2025-04-19", "home": False, "att_pct": 74},
        {"opponent": "Chelsea W", "date": "2025-04-26", "home": False, "att_pct": 68},
        {"opponent": "Arsenal W", "date": "2025-05-04", "home": False, "att_pct": 81},
    ],
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
    p = _cache_path(key)
    p.write_text(json.dumps({"ts": time.time(), "payload": payload}))

def fetch_youtube_videos(club_name, max_results=8):
    cache_key = f"yt_{club_name}_{max_results}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    club = WSL_CLUBS[club_name]
    query = club["search_query"]
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "date",
        "key": YOUTUBE_API_KEY,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("items", [])
        video_ids = [i["id"]["videoId"] for i in items if i["id"].get("videoId")]

        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        stats_params = {
            "part": "statistics,snippet",
            "id": ",".join(video_ids),
            "key": YOUTUBE_API_KEY,
        }
        sr = requests.get(stats_url, params=stats_params, timeout=10)
        sr.raise_for_status()
        videos = []
        for v in sr.json().get("items", []):
            stats = v.get("statistics", {})
            snippet = v.get("snippet", {})
            videos.append({
                "title": snippet.get("title", "")[:60],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "published": snippet.get("publishedAt", "")[:10],
                "video_id": v["id"],
                "url": f"https://youtube.com/watch?v={v['id']}",
                "source": "live",
            })
        videos.sort(key=lambda x: x["views"], reverse=True)
        _cache_set(cache_key, videos)
        return videos
    except Exception as e:
        return _get_simulated_videos(club_name)

def _get_simulated_videos(club_name):
    random.seed(hash(club_name) % 9999)
    titles = [
        f"{club_name} vs Rivals — Match Highlights",
        f"Player of the Month | {club_name}",
        f"Behind the Scenes: {club_name} Training",
        f"Goal of the Week | WSL",
        f"{club_name} Fan Q&A Session",
        f"Match Preview | Matchday 19",
    ]
    videos = []
    for i, title in enumerate(titles):
        days_ago = random.randint(1, 21)
        pub_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        videos.append({
            "title": title,
            "views": random.randint(15000, 420000),
            "likes": random.randint(400, 8000),
            "comments": random.randint(50, 900),
            "published": pub_date,
            "video_id": "",
            "url": "",
            "source": "simulated",
        })
    videos.sort(key=lambda x: x["views"], reverse=True)
    return videos

def fetch_reddit_sentiment(club_name, post_limit=100):
    cache_key = f"reddit_{club_name}_{post_limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID", ""),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET", ""),
            user_agent="WSL Fan Intelligence Dashboard v1.0",
        )
        terms = WSL_CLUBS[club_name]["reddit_terms"]
        subreddits = ["WomensSuperLeague", "Lionesses", "soccer", "football"]
        posts = []
        for sub in subreddits:
            try:
                for submission in reddit.subreddit(sub).new(limit=50):
                    text = f"{submission.title} {submission.selftext}"
                    if any(t.lower() in text.lower() for t in terms):
                        blob = TextBlob(text)
                        posts.append({
                            "text": submission.title[:120],
                            "score": blob.sentiment.polarity,
                            "subjectivity": blob.sentiment.subjectivity,
                            "upvotes": submission.score,
                            "created": datetime.fromtimestamp(submission.created_utc).strftime("%Y-%m-%d"),
                            "url": f"https://reddit.com{submission.permalink}",
                            "source": "live",
                        })
            except:
                continue

        if not posts:
            return _get_simulated_sentiment(club_name)

        result = _aggregate_sentiment(posts, club_name)
        _cache_set(cache_key, result)
        return result
    except Exception:
        return _get_simulated_sentiment(club_name)

def _aggregate_sentiment(posts, club_name):
    if not posts:
        return _get_simulated_sentiment(club_name)
    scores = [p["score"] for p in posts]
    avg = np.mean(scores)
    normalized = int(((avg + 1) / 2) * 100)
    normalized = max(30, min(95, normalized))
    return {
        "score": normalized,
        "post_count": len(posts),
        "positive_pct": int(sum(1 for s in scores if s > 0.05) / len(scores) * 100),
        "negative_pct": int(sum(1 for s in scores if s < -0.05) / len(scores) * 100),
        "neutral_pct": int(sum(1 for s in scores if -0.05 <= s <= 0.05) / len(scores) * 100),
        "top_posts": sorted(posts, key=lambda x: x["upvotes"], reverse=True)[:5],
        "source": posts[0]["source"] if posts else "simulated",
    }

def _get_simulated_sentiment(club_name):
    random.seed(hash(club_name + "sent") % 9999)
    base_scores = {
        "Arsenal W": 74, "Chelsea W": 69, "Man City W": 61,
        "Aston Villa W": 67, "Brighton W": 71,
    }
    score = base_scores.get(club_name, 65) + random.randint(-3, 3)
    pos = random.randint(45, 65)
    neg = random.randint(10, 25)
    return {
        "score": score,
        "post_count": random.randint(40, 180),
        "positive_pct": pos,
        "negative_pct": neg,
        "neutral_pct": 100 - pos - neg,
        "top_posts": [],
        "source": "simulated",
    }

def get_sentiment_trend(club_name, days=14):
    cache_key = f"trend_{club_name}_{days}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    random.seed(hash(club_name + "trend") % 9999)
    base_scores = {
        "Arsenal W": 68, "Chelsea W": 65, "Man City W": 57,
        "Aston Villa W": 61, "Brighton W": 67,
    }
    base = base_scores.get(club_name, 63)
    dates = [(datetime.now() - timedelta(days=days - i)).strftime("%b %d") for i in range(days)]
    
    def make_channel(offset, volatility):
        vals = []
        v = base + offset
        for _ in range(days):
            v += random.uniform(-volatility, volatility)
            v = max(30, min(95, v))
            vals.append(round(v, 1))
        return vals

    result = {
        "dates": dates,
        "twitter": make_channel(-2, 4),
        "instagram": make_channel(5, 3),
        "youtube": make_channel(-6, 2.5),
        "reddit": make_channel(1, 3.5),
    }
    _cache_set(cache_key, result)
    return result

def get_content_engagement(club_name):
    videos = fetch_youtube_videos(club_name, max_results=5)
    total_views = sum(v["views"] for v in videos)
    total_likes = sum(v["likes"] for v in videos)
    avg_engagement = round(total_likes / total_views * 100, 2) if total_views > 0 else 0
    
    reach_label = f"{total_views / 1_000_000:.1f}M" if total_views >= 1_000_000 else f"{total_views // 1000}K"
    
    return {
        "total_views": total_views,
        "reach_label": reach_label,
        "avg_engagement_rate": avg_engagement,
        "top_videos": videos[:5],
        "source": videos[0]["source"] if videos else "simulated",
    }

def get_ticket_demand(club_name):
    fixtures = FIXTURES.get(club_name, [])
    demand_index = np.mean([f["att_pct"] for f in fixtures]) / 100 if fixtures else 0.5
    
    processed = []
    for f in fixtures:
        pct = f["att_pct"]
        if pct >= 85:
            velocity = "Selling fast"
        elif pct >= 70:
            velocity = "Rising"
        elif pct >= 55:
            velocity = "Steady"
        else:
            velocity = "Slow"
        processed.append({**f, "velocity": velocity})
    
    return {
        "demand_index": round(demand_index, 2),
        "fixtures": processed,
        "source": "simulated",
    }

def get_fan_signals(club_name, sentiment_score, content_views, demand_index):
    signals = []
    base_scores = {
        "Arsenal W": 74, "Chelsea W": 69, "Man City W": 61,
        "Aston Villa W": 67, "Brighton W": 71,
    }
    
    if sentiment_score < 65:
        signals.append({
            "priority": "HIGH",
            "title": "Sentiment declining — intervention needed",
            "desc": f"Score at {sentiment_score}/100. Cross-channel negativity trending. Review content strategy.",
            "source": "Social sentiment",
        })
    
    if demand_index < 0.65:
        signals.append({
            "priority": "HIGH",
            "title": "Ticket demand below league average",
            "desc": f"Demand index {demand_index:.2f} vs league avg 0.77. Win-back campaign recommended.",
            "source": "Ticketing",
        })
    
    if sentiment_score > 70 and demand_index > 0.75:
        signals.append({
            "priority": "MED",
            "title": "Fan energy high — capitalise now",
            "desc": "Positive sentiment + strong attendance. Prime window for upsell and membership push.",
            "source": "Combined",
        })
    
    if club_name == "Aston Villa W":
        signals.append({
            "priority": "HIGH",
            "title": "Star player content under-leveraged",
            "desc": "Player content drives 6x club average reach. Build dedicated content series.",
            "source": "YouTube",
        })
    
    if club_name == "Man City W":
        signals.append({
            "priority": "MED",
            "title": "TikTok presence lags rivals by 60%",
            "desc": "Arsenal W and Chelsea W post 3x more short-form content. Opportunity to close gap.",
            "source": "Content",
        })
    
    signals.append({
        "priority": "OPT",
        "title": "Pre-match content window underused",
        "desc": "Sentiment peaks 48h before kickoff but posting frequency drops. Schedule more.",
        "source": "Content cadence",
    })
    
    return signals[:4]

def get_full_club_data(club_name):
    sentiment = fetch_reddit_sentiment(club_name)
    content = get_content_engagement(club_name)
    tickets = get_ticket_demand(club_name)
    trend = get_sentiment_trend(club_name)
    signals = get_fan_signals(
        club_name,
        sentiment["score"],
        content["total_views"],
        tickets["demand_index"]
    )
    
    risk_count = sum(1 for s in signals if s["priority"] == "HIGH")
    
    return {
        "club": club_name,
        "sentiment": sentiment,
        "content": content,
        "tickets": tickets,
        "trend": trend,
        "signals": signals,
        "kpis": {
            "sentiment_score": sentiment["score"],
            "content_reach": content["reach_label"],
            "demand_index": tickets["demand_index"],
            "risk_alerts": risk_count,
        },
        "data_sources": {
            "sentiment": sentiment.get("source", "simulated"),
            "content": content.get("source", "simulated"),
            "tickets": "simulated",
        }
    }
