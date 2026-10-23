# Weather-Aware Truck Routing

A React + Django web app that helps a truck driver pick the safest route by
weather, load weight and travel time.

> Planning aid only. It does not guarantee that a route is safe or legally
> compliant.

**Status:** in progress. The backend API works end to end and is tested;
the frontend is next.

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

## Key decisions

- **Wind:** sustained wind; gusts shown as info only.
- **Edges:** lower bound inclusive (rain 0.25 → High); rain 1.00 and
  snow 3.0 are Severe (No Travel is strictly `>`).
- **Checkpoint risk:** the worst of wind / rain / snow, after load rules.
- **Miles at a level:** each checkpoint covers the miles since the previous one.
- **Average risk:** Low=0 … No Travel=4, weighted by miles.
- **No Travel:** never recommended if another route has none.
- **Missing weather:** shown as unknown, never as Low.

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

`POST /api/plan` — plans a trip.

```json
{ "origin": "Chicago, IL", "destination": "Denver, CO",
  "departure": "2026-10-24T13:00:00Z", "load_lb": 42000, "interval_mi": 25 }
```

Returns the geocoded places, up to 3 routes (line, distance, time,
checkpoints with ETA, weather and risk, risk summary), the recommended route
with the reason, and the heatmap (grid points × 49 hourly risk values,
hour 0 = departure).

Errors: `{"error": "<code>", "message": "..."}` — `invalid_input` (400, plus
`fields`), `place_not_found` / `no_route` (404), `routing_unavailable` /
`weather_unavailable` / `weather_rate_limited` (502).

## Limitations

- Forecasts get less accurate further ahead.
