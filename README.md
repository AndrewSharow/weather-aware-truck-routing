# Weather-Aware Truck Routing

A React + Django web app that helps a truck driver pick the safest route by
weather, load weight and travel time.

> Planning aid only. It does not guarantee that a route is safe or legally
> compliant.

**Status:** in progress. Risk classification, route recommendation and
checkpoint sampling and the HERE client are done and tested; the weather
client is next.

## What it does

The driver enters origin, destination, departure time, load weight (lb) and a
checkpoint interval (10 / 25 / 50 miles). The app:

1. Gets up to 3 truck routes from HERE.
2. Places a checkpoint every N miles and estimates the truck's arrival time
   (ETA) at each one.
3. Gets the hourly forecast for each checkpoint **at its ETA** (Open-Meteo).
4. Classifies risk per checkpoint using the thresholds and load rules below.
5. Recommends one route.
6. Shows routes, checkpoints, risk levels, ETAs and route summaries on a map,
   plus a weather-risk heatmap along the trip corridor with a 0–48 h slider.

## Stack

| Part | Choice |
|---|---|
| Backend | Python 3.12, Django 5.2, Django REST Framework |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Map | MapLibre GL JS (`react-map-gl`) + OpenFreeMap tiles |
| Routing + geocoding | HERE Routing API v8 (truck mode) + HERE Geocoding & Search |
| Weather | Open-Meteo hourly forecast |
| Hosting | Railway (backend), Vercel (frontend) |

All external API calls go through the backend, so the HERE key never reaches
the browser.

## Risk rules

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind (mph) | <25 | 25–34 | 35–44 | 45–54 | ≥55 |
| Rain (in/hr) | <0.10 | 0.10–0.25 | 0.25–0.50 | 0.50–1.00 | >1.00 |
| Snow (in/hr) | <0.5 | 0.5–1.0 | 1.0–2.0 | 2.0–3.0 | >3.0 |

Load rules: ≥55 mph → No Travel for any load · 45–54 mph and load >30,000 lb →
No Travel · 35–44 mph and load >40,000 lb → Severe.

Recommendation order: fewest Severe miles → fewest High miles → lowest average
risk → shortest travel time.

## Decisions

- **Wind:** sustained wind is used for the rules; gusts are shown as info only.
- **Edges:** lower bound is inclusive (rain 0.25 → High, snow 1.0 → High).
  No Travel for rain and snow is strictly `>` as in the table, so rain 1.00
  and snow 3.0 are Severe.
- **Checkpoint risk** = the worst of wind / rain / snow, after load rules.
- **Rain / snow rate:** Open-Meteo gives the amount that falls in each hour.
  That amount is the average rate for that hour (in/hr).
- **Checkpoints:** placed every N miles from the origin, plus one at the
  destination. Each checkpoint covers the miles since the previous one
  (the last one covers the remainder).
- **ETA:** departure + HERE's travel time up to that point. HERE returns
  travel time per stretch of road (`spans=duration,functionalClass`: a new
  span starts when the road type changes, e.g. city street → highway), so
  slow and fast parts get correct ETAs; inside a span, time is split by
  distance.
- **Geocoding:** USA only, best match. Matches with a HERE `queryScore`
  below 0.7 are treated as "place not found" (e.g. random text).
- **Miles at a level:** each checkpoint's covered miles count at its level.
- **Average risk:** Low=0 … No Travel=4, weighted by miles.
- **No Travel:** a route with any No Travel miles is never recommended if
  another route has none. It is shown with a warning.
- **Ranking:** No Travel miles → Severe miles → High miles → average risk →
  travel time. Miles are compared rounded to 0.1 mi. The first rule that
  separates the best route from the runner-up is shown as the reason
  (e.g. "Fewest Severe miles"). A full tie keeps HERE's order.
- **Unknown miles** are reported per route but are not part of the ranking;
  the average risk uses known miles only.
- **Weight:** the risk rules use the **load**. HERE needs the **gross**
  vehicle weight, so we send load + 35,000 lb (assumed empty tractor-trailer).
  Max load is 45,000 lb, so gross stays ≤ 80,000 lb.
- **Forecast range:** departure up to 7 days ahead. Hours without forecast
  data are shown as **unknown** (grey), never as Low.
- **Heatmap slider:** hour 0 = departure time.
- **Time:** UTC in the backend; the UI shows the browser's timezone.

## Run locally

Backend (needs Python 3.10+, developed on 3.12):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your HERE_API_KEY
python manage.py runserver
```

Check: `curl localhost:8000/api/health` → `{"status": "ok"}`

Tests: `python manage.py test`

## API

`GET /api/health` — server check.

`POST /api/plan` — coming next.

## Limitations

- Forecasts get less accurate further ahead.
