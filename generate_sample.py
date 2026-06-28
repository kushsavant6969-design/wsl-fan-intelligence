"""Generate sample CSV for FanIQ — 300 fans, sport-agnostic."""
import pandas as pd
import numpy as np
from datetime import date, timedelta
import random

FOOTBALL_PLAYERS = [
    "Marcus Rashford", "Bukayo Saka", "Harry Kane", "Jude Bellingham",
    "Erling Haaland", "Mohamed Salah", "Virgil van Dijk", "Trent Alexander-Arnold",
]
CRICKET_PLAYERS = [
    "Virat Kohli", "Ben Stokes", "Joe Root", "Babar Azam",
    "Pat Cummins", "Rohit Sharma", "Steve Smith", "Jasprit Bumrah",
]
ALL_PLAYERS = FOOTBALL_PLAYERS + CRICKET_PLAYERS

MEMBERSHIP_TYPES = ["None", "Bronze", "Silver", "Gold", "Platinum"]
CHANNELS = ["Email", "SMS", "Push Notification", "Social", "Direct Mail"]
COUNTRIES = [
    "England", "India", "Australia", "Pakistan", "USA",
    "Nigeria", "South Africa", "Germany", "Spain", "Canada",
    "Bangladesh", "Sri Lanka", "New Zealand", "UAE", "Kenya",
]
COUNTRY_WEIGHTS = [0.22, 0.15, 0.10, 0.08, 0.07, 0.05, 0.05, 0.04, 0.04, 0.04,
                   0.04, 0.03, 0.03, 0.03, 0.03]

TODAY = date(2026, 6, 28)


def generate_sample_data(n: int = 300) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    random.seed(42)

    fan_ids = [f"FAN{i:04d}" for i in range(1, n + 1)]
    ages = np.clip(rng.normal(34, 13, n).astype(int), 16, 75)
    genders = rng.choice(["Male", "Female", "Non-binary"], n, p=[0.55, 0.38, 0.07])
    countries = rng.choice(COUNTRIES, n, p=COUNTRY_WEIGHTS)

    mem_types = rng.choice(MEMBERSHIP_TYPES, n, p=[0.28, 0.22, 0.22, 0.18, 0.10])
    mem_order = {"None": 0, "Bronze": 1, "Silver": 2, "Gold": 3, "Platinum": 4}
    mem_rank = np.array([mem_order[m] for m in mem_types])

    # Last attended — higher tier = more recent
    last_attended = []
    for m in mem_types:
        if m == "None":
            offset = random.randint(300, 900)
        elif m == "Bronze":
            offset = random.randint(90, 400)
        elif m == "Silver":
            offset = random.randint(30, 200)
        elif m == "Gold":
            offset = random.randint(7, 90)
        else:  # Platinum
            offset = random.randint(0, 30)
        last_attended.append((TODAY - timedelta(days=offset)).isoformat())

    # Tickets purchased
    tickets = np.array([
        max(0, int(rng.normal((mem_rank[i] + 1) * 3, 2))) for i in range(n)
    ])

    # Spend
    spend_ranges = {"None": (0, 50), "Bronze": (50, 200), "Silver": (150, 500),
                    "Gold": (400, 1200), "Platinum": (900, 3000)}
    spend = np.array([round(rng.uniform(*spend_ranges[m]), 2) for m in mem_types])

    # Engagement score (0-100 raw, percentile calibrated later)
    base_eng = mem_rank * 15 + rng.normal(30, 18, n)
    engagement_scores = np.clip(base_eng, 1, 99).astype(int)

    # Channel preference
    channel_prefs = []
    for i, age in enumerate(ages):
        if age < 25:
            channel_prefs.append(rng.choice(["Push Notification", "Social", "SMS"], p=[0.45, 0.40, 0.15]))
        elif age < 40:
            channel_prefs.append(rng.choice(["Email", "Push Notification", "Social"], p=[0.40, 0.35, 0.25]))
        else:
            channel_prefs.append(rng.choice(["Email", "SMS", "Direct Mail"], p=[0.55, 0.30, 0.15]))

    # Favourite player — mix of football and cricket
    fav_players = []
    for country in countries:
        if country in ["India", "Pakistan", "Australia", "Bangladesh", "Sri Lanka",
                       "New Zealand", "South Africa"]:
            pool = CRICKET_PLAYERS + FOOTBALL_PLAYERS[:4]
        else:
            pool = FOOTBALL_PLAYERS + CRICKET_PLAYERS[:4]
        fav_players.append(random.choice(pool))

    return pd.DataFrame({
        "Fan_ID": fan_ids,
        "Age": ages,
        "Gender": genders,
        "Country": countries,
        "Membership_Type": mem_types,
        "Last_Attended": last_attended,
        "Tickets_Purchased": tickets,
        "Spend": spend,
        "Engagement_Score": engagement_scores,
        "Channel_Preference": channel_prefs,
        "Favourite_Player": fav_players,
    })


def generate_template() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "Fan_ID", "Age", "Gender", "Last_Attended", "Tickets_Purchased",
        "Spend", "Membership_Type", "Engagement_Score", "Channel_Preference",
        "Country", "Favourite_Player",
    ])


if __name__ == "__main__":
    df = generate_sample_data(300)
    df.to_csv("faniq_sample.csv", index=False)
    print(f"Generated faniq_sample.csv — {len(df)} rows, {len(df.columns)} columns")
