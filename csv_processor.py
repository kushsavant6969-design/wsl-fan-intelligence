"""
csv_processor.py — WSL FanIntel CSV upload processor

Handles:
  - Column detection via rapidfuzz fuzzy matching (no confirm step)
  - CSV-driven data computation (replaces hardcoded WSL_CLUBS)
  - Feature gating based on detected columns
  - Hybrid schema: <4 core columns matched → limited feature set
  - Percentile-based churn calibration
  - PDF-safe text helper
"""

import random as _rnd
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── Canonical column registry ─────────────────────────────────────────────────
CANONICAL_COLUMNS = {
    "Fan_ID":            ["fan_id","fanid","id","fan id","customer_id","customerid","member_id","uid","fan_number"],
    "Age":               ["age","fan_age","age_years","age_band","fan_age_years","customer_age"],
    "Gender":            ["gender","sex","fan_gender","customer_gender"],
    "Last_Attended":     ["last_attended","last_attendance","last_visit","last_ticket_date","last_match",
                          "date_last_attended","last_game","date_of_last_attendance"],
    "Tickets_Purchased": ["tickets_purchased","tickets","num_tickets","ticket_count","tickets_bought",
                          "total_tickets","ticket_quantity","number_of_tickets"],
    "Spend":             ["spend","total_spend","revenue","total_revenue","fan_spend","ltv",
                          "lifetime_value","customer_spend","cumulative_spend"],
    "Favourite_Player":  ["favourite_player","favorite_player","fav_player","preferred_player",
                          "top_player","fav player","favourite player"],
    "Channel_Preference":["channel_preference","preferred_channel","channel","comms_channel",
                          "pref_channel","communication_channel"],
    "Membership_Type":   ["membership_type","membership","fan_type","tier","subscription_type",
                          "member_type","fan_tier"],
    "Postcode_District": ["postcode_district","postcode","postal_code","zip_code","district",
                          "area_code","zip"],
}

# Columns that unlock the full feature set
CORE_COLUMNS = {"Fan_ID", "Age", "Last_Attended", "Tickets_Purchased"}

# Feature gate: canonical columns needed to unlock each feature
# Note: "sentiment" is always available — FanIntel derives it from uploaded signals
FEATURE_GATES = {
    "fan_cohorts":           {"Age"},
    "churn_risk":            {"Last_Attended"},
    "attendance_prediction": {"Last_Attended", "Tickets_Purchased"},
    "player_intelligence":   {"Favourite_Player"},
    "commercial_impact":     {"Spend"},
    "campaign_recs":         {"Channel_Preference"},
    "sentiment":             set(),   # always computed by FanIntel
    "geo_analysis":          {"Postcode_District"},
}


# ── Column detection ──────────────────────────────────────────────────────────

def detect_columns(df: pd.DataFrame) -> dict:
    """
    Auto-detect canonical column names in DataFrame using rapidfuzz.
    Returns {canonical_name: actual_column_name} for all matched columns.
    No confirmation step — auto-applied.
    """
    col_map = {}
    df_cols_norm = {
        c.lower().replace(" ", "_").replace("-", "_"): c
        for c in df.columns
    }

    # Flat variant → canonical lookup
    variant_to_canonical = {}
    for canonical, variants in CANONICAL_COLUMNS.items():
        for v in variants:
            variant_to_canonical[v.lower().replace(" ", "_")] = canonical

    try:
        from rapidfuzz import process, fuzz
        all_variants = list(variant_to_canonical.keys())
        for norm_col, orig_col in df_cols_norm.items():
            result = process.extractOne(
                norm_col, all_variants, scorer=fuzz.ratio, score_cutoff=72
            )
            if result:
                canonical = variant_to_canonical[result[0]]
                if canonical not in col_map:
                    col_map[canonical] = orig_col
    except ImportError:
        # Fallback: exact lowercase match only
        for norm_col, orig_col in df_cols_norm.items():
            if norm_col in variant_to_canonical:
                canonical = variant_to_canonical[norm_col]
                if canonical not in col_map:
                    col_map[canonical] = orig_col

    return col_map


def check_features(col_map: dict) -> dict:
    """Returns {feature_name: bool} indicating which features are available."""
    detected = set(col_map.keys())
    return {feat: gates.issubset(detected) for feat, gates in FEATURE_GATES.items()}


def is_full_schema(col_map: dict) -> bool:
    """True if at least 4 core columns are detected."""
    return len(set(col_map.keys()).intersection(CORE_COLUMNS)) >= 4


# ── Helpers ───────────────────────────────────────────────────────────────────

def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def _dates(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_datetime(df[col], errors="coerce")


def _days_since(df: pd.DataFrame, col: str) -> pd.Series:
    return (datetime.now() - _dates(df, col)).dt.days.clip(lower=0)


def _compute_fan_engagement(df: pd.DataFrame, col_map: dict) -> pd.Series:
    """
    Derive a per-fan FanIntel Engagement Score (0–100) from available signals.
    Uses recency (Last_Attended), frequency (Tickets_Purchased), and spend
    signals — whichever are present. Never reads an Engagement_Score column;
    this metric is always FanIntel-calculated.
    """
    parts = []
    if "Last_Attended" in col_map:
        days = _days_since(df, col_map["Last_Attended"])
        # Recency: 0 days→100, 365+ days→20
        recency = (100.0 - (days.clip(0, 365) / 365.0 * 80.0)).clip(20.0, 100.0)
        parts.append(recency.values)
    if "Tickets_Purchased" in col_map:
        tkts = _num(df, col_map["Tickets_Purchased"])
        max_t = max(float(tkts.quantile(0.95)), 1.0)
        freq = (20.0 + (tkts.clip(0, max_t) / max_t * 70.0)).clip(20.0, 90.0)
        parts.append(freq.values)
    if "Spend" in col_map:
        spend = _num(df, col_map["Spend"])
        max_s = max(float(spend.quantile(0.95)), 1.0)
        spend_sc = (20.0 + (spend.clip(0, max_s) / max_s * 70.0)).clip(20.0, 90.0)
        parts.append(spend_sc.values)
    if parts:
        return pd.Series(np.mean(parts, axis=0), index=df.index).round(1)
    return pd.Series([65.0] * len(df), index=df.index)


def _pdf_safe(text: str) -> str:
    """Strip / replace unicode chars that FPDF's latin-1 encoder rejects."""
    return (
        str(text)
        .replace("—", " - ").replace("–", "-")
        .replace("•", "-").replace("’", "'")
        .replace("‘", "'").replace("“", '"')
        .replace("”", '"').replace(" ", " ")
        .encode("latin-1", errors="replace").decode("latin-1")
    )


# ── KPI computation ───────────────────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame, col_map: dict) -> dict:
    kpis = {}
    total = len(df)

    # FanIntel Engagement Score — always derived from uploaded signals
    _eng = _compute_fan_engagement(df, col_map)
    kpis["sentiment_score"] = int(round(float(_eng.mean())))

    # Ticket demand ← Tickets_Purchased (fraction of fans who bought ≥1)
    if "Tickets_Purchased" in col_map:
        tkts = _num(df, col_map["Tickets_Purchased"])
        active_pct = float((tkts > 0).mean())
        kpis["demand_index"] = round(active_pct, 2)
    else:
        kpis["demand_index"] = 0.70

    # Recency score ← Last_Attended
    recency_score = 60.0
    if "Last_Attended" in col_map:
        days = _days_since(df, col_map["Last_Attended"])
        avg_days = float(days.mean())
        recency_score = min(100.0, max(0.0, avg_days / 3.65))

    # Overall fan risk
    sent = kpis["sentiment_score"]
    demand_pct = kpis["demand_index"] * 100
    overall_risk = round(
        (100 - sent) * 0.35 + (100 - demand_pct) * 0.30 + recency_score * 0.35, 1
    )
    kpis["overall_risk"] = float(max(5.0, min(95.0, overall_risk)))

    # Content reach placeholder
    kpis["content_reach"] = f"{total:,} fans"

    # Risk alerts: updated after churn is computed; placeholder for now
    kpis["risk_alerts"] = 0

    return kpis


# ── Cohort computation ────────────────────────────────────────────────────────

_COHORT_ACTIONS = {
    "18–24 Casual": {
        "channel": "TikTok + Instagram",
        "timing":  "48 hr before next home fixture",
        "trigger": "No attendance in 60 days",
        "offer":   "£5 off first ticket",
    },
    "25–34 Regular": {
        "channel": "Email + App push notification",
        "timing":  "3 weeks before season ticket window opens",
        "trigger": "Season ticket not yet renewed",
        "offer":   "Priority seat selection + early-bird price lock",
    },
    "35–49 Loyalist": {
        "channel": "Email + Direct mail",
        "timing":  "Day 7 of renewal window if not yet completed",
        "trigger": "Renewal not completed",
        "offer":   "Complimentary hospitality upgrade voucher",
    },
    "50+ Veteran": {
        "channel": "Email + personalised letter",
        "timing":  "End of season",
        "trigger": "Multi-year membership anniversary",
        "offer":   "Legacy recognition + personalised captain's letter",
    },
    "Lapsed Buyers": {
        "channel": "Email + SMS",
        "timing":  "Next derby announcement",
        "trigger": "No attendance in 180+ days",
        "offer":   "30% win-back discount + 'what you missed' highlight reel",
    },
}


def compute_cohorts(df: pd.DataFrame, col_map: dict) -> list:
    total = len(df)
    cohorts = []
    if "Age" not in col_map:
        return cohorts

    ages = _num(df, col_map["Age"])
    bands = [
        ("18–24 Casual",   18,  24),
        ("25–34 Regular",  25,  34),
        ("35–49 Loyalist", 35,  49),
        ("50+ Veteran",    50, 200),
    ]

    for name, lo, hi in bands:
        mask = ((ages >= lo) & (ages <= hi)).values
        count = int(mask.sum())
        size_pct = round(count / total * 100)

        risk_score = 50
        engagement = 50

        if "Last_Attended" in col_map and count > 0:
            days = _days_since(df, col_map["Last_Attended"])
            band_days = days[mask[:len(days)]]
            if not band_days.empty:
                risk_score = int(min(95, max(10, float(band_days.mean()) / 3.65)))

        if count > 0:
            fan_eng = _compute_fan_engagement(df, col_map)
            band_eng = fan_eng[mask[:len(fan_eng)]]
            if not band_eng.empty:
                engagement = int(round(float(band_eng.mean())))

        act = _COHORT_ACTIONS[name]
        cohorts.append({
            "name":       name,
            "size_pct":   size_pct,
            "risk_score": risk_score,
            "engagement": engagement,
            "count":      count,
            "action":     f"{act['channel']} · {act['timing']} · trigger: {act['trigger']}",
            "channel":    act["channel"],
            "timing":     act["timing"],
            "trigger":    act["trigger"],
            "offer":      act["offer"],
            "source":     "from_data",
        })

    # Lapsed cohort (Last_Attended > 180 days)
    if "Last_Attended" in col_map:
        days = _days_since(df, col_map["Last_Attended"])
        lapsed_mask = (days > 180).values
        lapsed_count = int(lapsed_mask.sum())
        if lapsed_count > 0:
            act = _COHORT_ACTIONS["Lapsed Buyers"]
            lapsed_days = days[lapsed_mask[:len(days)]]
            cohorts.append({
                "name":       "Lapsed Buyers",
                "size_pct":   round(lapsed_count / total * 100),
                "risk_score": int(min(95, float(lapsed_days.mean()) / 3.65)),
                "engagement": 15,
                "count":      lapsed_count,
                "action":     f"{act['channel']} · {act['timing']} · trigger: {act['trigger']}",
                "channel":    act["channel"],
                "timing":     act["timing"],
                "trigger":    act["trigger"],
                "offer":      act["offer"],
                "source":     "from_data",
            })

    return cohorts


# ── Churn risk (percentile-based calibration) ─────────────────────────────────

def compute_churn_risks(df: pd.DataFrame, col_map: dict) -> list:
    if "Last_Attended" not in col_map:
        return []

    days = _days_since(df, col_map["Last_Attended"])
    p25 = float(days.quantile(0.25))
    p90 = float(days.quantile(0.90))

    PROFILES = [
        {"name": "18–24 Casual",   "age_lo": 18, "age_hi": 24,  "base": 38, "is_lapsed": False,
         "retention": "TikTok-first content series + £5 first-ticket discount code"},
        {"name": "25–34 Regular",  "age_lo": 25, "age_hi": 34,  "base": 22, "is_lapsed": False,
         "retention": "Early-bird season ticket offer + priority seat selection window"},
        {"name": "35–49 Loyalist", "age_lo": 35, "age_hi": 49,  "base": 11, "is_lapsed": False,
         "retention": "Auto-renewal prompt + complimentary hospitality upgrade voucher"},
        {"name": "50+ Veteran",    "age_lo": 50, "age_hi": 200, "base":  8, "is_lapsed": False,
         "retention": "Legacy membership recognition + personalised captain's letter"},
        {"name": "Lapsed Buyers",  "age_lo":  0, "age_hi": 200, "base": 72, "is_lapsed": True,
         "retention": "Win-back email: 30% off + personalised 'what you missed' reel"},
    ]

    results = []
    for p in PROFILES:
        if p["is_lapsed"]:
            mask = (days > 180).values
        elif "Age" in col_map:
            ages = _num(df, col_map["Age"])
            mask = ((ages >= p["age_lo"]) & (ages <= p["age_hi"])).values
        else:
            mask = np.ones(len(df), dtype=bool)

        band_days = days[mask[:len(days)]]
        if len(band_days) == 0:
            churn = float(p["base"])
        else:
            avg_d = float(band_days.mean())
            ratio = (avg_d - p25) / max(p90 - p25, 1.0)
            churn = p["base"] + ratio * 30.0
            churn = max(3.0, min(95.0, churn))

        results.append({
            "name":             p["name"],
            "churn_pct":        round(churn, 1),
            "retention_action": p["retention"],
            "risk_level":       "HIGH" if churn >= 55 else "MED" if churn >= 28 else "LOW",
            "source":           "from_data",
        })
    return results


# ── Player influence ──────────────────────────────────────────────────────────

def compute_player_influence(df: pd.DataFrame, col_map: dict) -> list:
    if "Favourite_Player" not in col_map:
        return []

    player_col = col_map["Favourite_Player"]
    total = len(df)
    counts = df[player_col].value_counts()

    fan_eng = _compute_fan_engagement(df, col_map)
    overall_eng = float(fan_eng.mean())

    results = []
    for player, cnt in counts.head(10).items():
        if pd.isna(player) or str(player).strip() == "":
            continue
        pct = cnt / total
        mask = (df[player_col] == player).values

        eng_val = overall_eng
        peng = fan_eng[mask[:len(fan_eng)]]
        if not peng.empty:
            eng_val = float(peng.mean())

        lift = round(eng_val - overall_eng, 1)
        mult = round(eng_val / overall_eng, 1) if overall_eng > 0 else 1.0
        merch = min(100, int(pct * 500))
        mval = int(round(lift * 3 + mult * 10 + merch * 0.5))

        results.append({
            "name":            str(player),
            "position":        "—",
            "club":            "Your Club",
            "sentiment_lift":  lift,
            "engagement_mult": mult,
            "merch_index":     merch,
            "marketing_value": mval,
            "fan_count":       int(cnt),
            "source":          "from_data",
        })
    return sorted(results, key=lambda x: x["marketing_value"], reverse=True)


# ── Signal generation ─────────────────────────────────────────────────────────

def generate_csv_signals(df: pd.DataFrame, col_map: dict, kpis: dict) -> list:
    signals = []
    total = len(df)
    sentiment = kpis.get("sentiment_score", 65)
    demand = kpis.get("demand_index", 0.70)

    # Lapsed fans
    if "Last_Attended" in col_map:
        days = _days_since(df, col_map["Last_Attended"])
        lapsed_pct = round(float((days > 180).mean()) * 100)
        if lapsed_pct > 20:
            signals.append({
                "priority": "HIGH",
                "title":    f"{lapsed_pct}% of fans lapsed (180+ days)",
                "desc":     (
                    f"{int(total * lapsed_pct / 100):,} fans haven't attended in 6+ months. "
                    "Immediate win-back opportunity before next home fixture."
                ),
                "source":   "From your data",
                "action":   "Launch win-back email series with 30% discount + matchday reel",
            })

    # Low engagement — derived from FanIntel engagement score
    fan_eng = _compute_fan_engagement(df, col_map)
    low_eng_pct = round(float((fan_eng < 30).mean()) * 100)
    if low_eng_pct > 20:
        signals.append({
            "priority": "HIGH",
            "title":    f"{low_eng_pct}% of fans have low engagement",
            "desc":     (
                "FanIntel's engagement model shows a large segment scoring below 30/100. "
                "Digital re-engagement campaign needed — personalised content by channel."
            ),
            "source":   "FanIntel",
            "action":   "Personalised digital re-engagement campaign by preferred channel",
        })

    # Ticket demand
    if demand < 0.65:
        signals.append({
            "priority": "HIGH" if demand < 0.50 else "MED",
            "title":    f"Ticket conversion gap — only {round(demand * 100)}% active buyers",
            "desc":     (
                f"Only {round(demand * 100)}% of your fan database has purchased tickets. "
                "The non-buyer segment is the biggest short-term revenue opportunity."
            ),
            "source":   "From your data",
            "action":   "Targeted ticket campaign to non-buyer segments",
        })

    # Top 20% revenue concentration
    if "Spend" in col_map:
        spend = _num(df, col_map["Spend"])
        top20_thr = float(spend.quantile(0.80))
        top20_share = float(spend[spend >= top20_thr].sum() / spend.sum() * 100)
        signals.append({
            "priority": "MED",
            "title":    f"Top 20% of fans drive {round(top20_share)}% of revenue",
            "desc":     (
                "Revenue is highly concentrated — consistent with WSL top-tier pattern. "
                "Protecting this cohort via VIP loyalty is a critical commercial lever."
            ),
            "source":   "From your data",
            "action":   "Introduce tiered VIP loyalty scheme for top 20% spenders",
        })

    # Pre-match content window (modelled insight)
    signals.append({
        "priority": "OPT",
        "title":    "Pre-match content window underused",
        "desc":     "Fan engagement peaks 48 hr before kickoff — schedule 2 posts per match window.",
        "source":   "Modelled",
        "action":   "Automate pre-match content scheduler",
    })

    return signals[:4]


# ── Attendance predictions ────────────────────────────────────────────────────

def compute_attendance_predictions(df: pd.DataFrame, col_map: dict, kpis: dict) -> list:
    rng = _rnd.Random(hash(str(len(df))) % 99999)
    sentiment = kpis.get("sentiment_score", 65)
    base_att = round(kpis.get("demand_index", 0.70) * 100)

    fixtures = [
        {"opponent": "Next Home Fixture",  "date": "TBC", "home": True,  "is_rival": False, "days_away": 7},
        {"opponent": "Away Fixture",        "date": "TBC", "home": False, "is_rival": False, "days_away": 14},
        {"opponent": "Derby / Big Fixture", "date": "TBC", "home": True,  "is_rival": True,  "days_away": 21},
    ]

    preds = []
    for f in fixtures:
        sent_adj    = (sentiment - 60) * 0.15
        derby_bonus = 10 if f["is_rival"] else 0
        days_adj    = max(0, (20 - f["days_away"]) / 20) * 4
        predicted   = base_att + sent_adj + derby_bonus + days_adj + rng.uniform(-2, 2)
        predicted   = max(15, min(100, predicted))
        conf = rng.uniform(4, 8)
        preds.append({
            **f,
            "predicted_pct":   round(predicted, 1),
            "confidence_low":  round(max(10, predicted - conf), 1),
            "confidence_high": round(min(100, predicted + conf), 1),
            "at_risk":         predicted < 70,
            "att_pct":         round(predicted),
            "drivers": {
                "historical":    base_att,
                "sentiment_adj": round(sent_adj, 1),
                "derby_bonus":   derby_bonus,
                "form_penalty":  0.0,
            },
            "source": "modelled",
        })
    return preds


# ── Sponsor exposure ──────────────────────────────────────────────────────────

def compute_sponsor_exposure(df: pd.DataFrame, col_map: dict, kpis: dict) -> dict:
    rng = _rnd.Random(hash(str(len(df)) + "sponsor") % 99999)
    sentiment = kpis.get("sentiment_score", 65)
    demand_pct = round(kpis.get("demand_index", 0.70) * 100)
    league_avg = 57

    fixtures = [
        {"opponent": "Next Home Fixture",  "date": "TBC", "home": True,  "is_rival": False, "att_pct": demand_pct},
        {"opponent": "Away Fixture",        "date": "TBC", "home": False, "is_rival": False, "att_pct": round(demand_pct * 0.9)},
        {"opponent": "Derby / Big Fixture", "date": "TBC", "home": True,  "is_rival": True,  "att_pct": min(100, round(demand_pct * 1.2))},
    ]

    scores = []
    for f in fixtures:
        content_score = min(100, sentiment * 0.8 + rng.uniform(10, 20))
        derby_mult    = 1.45 if f["is_rival"] else 1.0
        broadcast     = rng.uniform(65, 92) if f["is_rival"] else rng.uniform(28, 65)
        raw = (content_score * 0.30 + sentiment * 0.25 + broadcast * 0.28 + f["att_pct"] * 0.17)
        idx = round(min(100, max(10, raw * derby_mult)), 1)
        scores.append({
            **f,
            "sponsor_index":   idx,
            "vs_benchmark":    round(idx - league_avg, 1),
            "broadcast_reach": round(broadcast, 1),
            "is_premium":      idx >= 75,
            "source":          "modelled",
        })
    return {"fixtures": scores, "league_avg": league_avg}


# ── Content placeholder ───────────────────────────────────────────────────────

def compute_content_placeholder(df: pd.DataFrame, col_map: dict, kpis: dict) -> dict:
    return {
        "total_views":     0,
        "reach_label":     f"{len(df):,} fans",
        "engagement_rate": round(kpis.get("sentiment_score", 65) / 10.0, 2),
        "top_videos":      [],
        "source":          "csv",
    }


def compute_sentiment_trend_placeholder(kpis: dict, days: int = 14) -> dict:
    rng = _rnd.Random(hash(str(kpis.get("sentiment_score", 65))) % 9999)
    base = kpis.get("sentiment_score", 65)
    dates = [(datetime.now() - timedelta(days=days - i)).strftime("%b %d") for i in range(days)]

    def wave(offset, vol):
        v, vals = base + offset, []
        for _ in range(days):
            v += rng.uniform(-vol, vol)
            vals.append(round(max(30, min(95, v)), 1))
        return vals

    return {
        "dates":     dates,
        "twitter":   wave(-2, 4),
        "instagram": wave(5, 3),
        "youtube":   wave(-6, 2.5),
        "reddit":    wave(1, 3.5),
    }


# ── Master builder ────────────────────────────────────────────────────────────

def build_csv_data_dict(df: pd.DataFrame, col_map: dict) -> dict:
    """
    Build a data dict from uploaded CSV in the same format as get_full_club_data().
    Allows the entire dashboard rendering code to work unchanged.
    """
    from data import compute_fan_risk_score  # reuse existing risk engine

    kpis        = compute_kpis(df, col_map)
    cohorts     = compute_cohorts(df, col_map)
    churn_risks = compute_churn_risks(df, col_map)
    player_inf  = compute_player_influence(df, col_map)
    signals     = generate_csv_signals(df, col_map, kpis)
    att_preds   = compute_attendance_predictions(df, col_map, kpis)
    sponsor     = compute_sponsor_exposure(df, col_map, kpis)
    content     = compute_content_placeholder(df, col_map, kpis)
    trend       = compute_sentiment_trend_placeholder(kpis)
    features    = check_features(col_map)

    # Update risk_alerts from HIGH churn count
    kpis["risk_alerts"] = sum(1 for c in churn_risks if c["risk_level"] == "HIGH")

    # Fan risk via existing engine
    form = ["W", "D", "W", "L", "W"]
    fixtures_for_risk = [
        {"opponent": "Next Home Fixture",  "date": "TBC", "home": True,  "is_rival": False,
         "att_pct": round(kpis["demand_index"] * 100), "days_away":  7},
        {"opponent": "Away Fixture",        "date": "TBC", "home": False, "is_rival": False,
         "att_pct": round(kpis["demand_index"] *  95), "days_away": 14},
        {"opponent": "Derby / Big Fixture", "date": "TBC", "home": True,  "is_rival": True,
         "att_pct": min(100, round(kpis["demand_index"] * 120)), "days_away": 21},
    ]
    risk_data = compute_fan_risk_score("CSV Upload", kpis["sentiment_score"], fixtures_for_risk, form)
    kpis["overall_risk"] = risk_data["overall_risk"]

    # 30-day sentiment comparison (modelled)
    rng = _rnd.Random(hash(str(len(df))) % 9999)
    score_30d = max(35, min(95, kpis["sentiment_score"] + rng.randint(-8, 8)))
    pos_pct   = min(80, max(20, kpis["sentiment_score"] - 15))
    neg_pct   = max(5, 30 - (kpis["sentiment_score"] - 50) // 3)

    sentiment_dict = {
        "score":         kpis["sentiment_score"],
        "post_count":    len(df),
        "positive_pct":  pos_pct,
        "negative_pct":  neg_pct,
        "neutral_pct":   max(0, 100 - pos_pct - neg_pct),
        "score_30d_ago": score_30d,
        "source":        "csv",
    }

    return {
        "club":                   "Your Club",
        "sentiment":              sentiment_dict,
        "content":                content,
        "tickets":                {
            "demand_index": kpis["demand_index"],
            "fixtures": [
                {"opponent": "Next Fixture", "date": "TBC", "home": True, "att_pct": round(kpis["demand_index"] * 100),
                 "is_rival": False, "velocity": "Rising" if kpis["demand_index"] >= 0.70 else "Slow"},
            ],
        },
        "trend":                  trend,
        "signals":                signals,
        "risk_data":              risk_data,
        "league":                 {"position": "—", "pts": "—", "gd": "—"},
        "form":                   form,
        "form_comp":              ["WSL"] * len(form),
        "cohorts":                cohorts,
        "kpis":                   kpis,
        "data_sources":           {"sentiment": "fanIntel", "content": "csv"},
        "attendance_predictions": att_preds,
        "churn_risks":            churn_risks,
        "player_influence":       player_inf,
        "sponsor_exposure":       sponsor,
        # CSV-specific extras
        "col_map":    col_map,
        "features":   features,
        "csv_df":     df,
        "total_fans": len(df),
    }
