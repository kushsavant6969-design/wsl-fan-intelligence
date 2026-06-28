# FanIQ

Sport-agnostic fan segmentation and campaign intelligence platform.

Upload any fan database CSV. FanIQ auto-maps columns, scores every fan across five commercial dimensions, and generates ready-to-execute campaign briefs per segment.

## Tabs

- **Fan Dashboard** — Five score engine, segment donut, journey funnel, LTV distribution, top 10 tables
- **Campaign Intelligence** — Auto-generated campaign brief per segment with channel, offer, timing, and conversion estimate. PDF export.
- **Audience Story** — Narrative fanbase report designed for client presentations. PDF export.
- **Sponsorship Intelligence** — Pitch score, demographic breakdown, sponsor category recommendations. PDF export.
- **Player Influence** — Player commercial influence ranking (unlocks when Favourite_Player column present)

## Scoring Engine

Five scores (0–100, percentile-calibrated) computed per fan:

| Score | Inputs |
|---|---|
| Engagement | Engagement_Score column + Last_Attended recency |
| Commercial | Spend, Tickets_Purchased, Membership_Type |
| Loyalty | Last_Attended, Membership_Type, Tickets_Purchased |
| Churn Risk | Days since attendance, engagement inverse, spend inverse |
| Conversion Probability | Composite of Engagement + Commercial + (100 - Churn) |

**Segments:** VIP · High Potential · Regular · Win Back · Dormant

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Sample Data

Download from the upload screen or generate via:

```bash
python generate_sample.py   # creates faniq_sample.csv (300 rows)
```

## Deployment

Configured via `render.yaml`. Push to GitHub and connect to Render.
