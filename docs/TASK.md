# TASK — Weather-Aware Truck Routing

Source: `docs/fs-assessment-spotter.pdf`. Build a **React + Django** web app
that helps a truck driver choose the safest route by weather, load weight
and travel time.

## User inputs

- Origin and destination
- Departure date/time
- Load weight (lb)

## The app must

1. Get **3 route options** from a routing API (no own routing engine).
2. Sample weather every **10 / 25 / 50 miles**, using the truck's
   **estimated arrival time** at each checkpoint (forecast for that hour,
   not "now").
3. Classify risk at each checkpoint with the rules below.
4. **Recommend the best route** (order below).
5. Show on a **map**: all routes, checkpoints, risk levels, ETAs, route summaries.
6. Show a **weather heatmap along the trip corridor** with a **0–48 h
   forecast slider**.

Third-party APIs allowed for routing, geocoding, weather.

## Risk rules (per checkpoint)

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind (mph) | <25 | 25–34 | 35–44 | 45–54 | ≥55 |
| Rain (in/hr) | <0.10 | 0.10–0.25 | 0.25–0.50 | 0.50–1.00 | >1.00 |
| Snow (in/hr) | <0.5 | 0.5–1.0 | 1.0–2.0 | 2.0–3.0 | >3.0 |

Load rules:
- ≥55 mph → No Travel for any load
- 45–54 mph + >30,000 lb → No Travel
- 35–44 mph + >40,000 lb → Severe

## Recommendation order

1. Fewest Severe miles
2. Fewest High miles
3. Lowest average risk
4. Shortest travel time

## Deliverables

GitHub repo · hosted app · 5–10 min Loom walkthrough.

## Unclear points (decide, write the choice in README)

- **10 / 25 / 50 miles:** most likely a user choice of interval. Plan: a
  selector in the form.
- **Overlapping edges** (rain 0.25 is in Moderate AND High, snow 1.0, 2.0
  etc.): pick one rule, e.g. lower bound inclusive, and test it.
- **Checkpoint risk** = worst of wind / rain / snow, after load rules.
- **"Miles" at a level:** count each checkpoint's segment length (interval
  miles) at its risk level.
- **Average risk:** score Low=0, Moderate=1, High=2, Severe=3, No Travel=4,
  weighted by miles.
- **No Travel** on a route: never recommend it if another route has none;
  show a clear warning.
- **Wind:** sustained wind or gusts? Decide and explain.
- **Units:** weather API must return mph and in/hr (or convert).
