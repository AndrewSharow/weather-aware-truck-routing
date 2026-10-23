from datetime import datetime, timedelta
from string import ascii_uppercase
from typing import Any

from planner.clients.here import HereRoute, Place, geocode, truck_routes
from planner.clients.open_meteo import Forecast, HourlyWeather, fetch_forecast
from planner.heatmap import HOURS, HeatmapPoint, build_heatmap, corridor_grid
from planner.recommend import RouteOption, RouteSummary, level_key, recommend, summarize
from planner.risk import RiskLevel, checkpoint_risk
from planner.sampling import (
    Checkpoint,
    Point,
    elapsed_seconds,
    haversine_miles,
    sample_checkpoints,
)
from planner.serializers import PlanRequest

METERS_PER_MILE = 1609.344
LINE_MIN_MILES = 0.5

Assessed = tuple[Checkpoint, HourlyWeather, RiskLevel | None]


def plan_trip(request: PlanRequest) -> dict[str, Any]:
    origin = geocode(request.origin)
    destination = geocode(request.destination)
    routes = truck_routes(origin, destination, request.departure, request.load_lb)

    checkpoints = [checkpoints_for(route, request) for route in routes]
    anchors = [(c.lat, c.lon) for route in checkpoints for c in route]
    grid = corridor_grid(anchors)
    arrival = max(route[-1].eta for route in checkpoints)
    end = max(arrival, request.departure + timedelta(hours=HOURS - 1))
    forecast = fetch_forecast(anchors + grid, request.departure, end)

    route_ids = list(ascii_uppercase[: len(routes)])
    route_jsons = []
    options = []
    for route_id, route, route_checkpoints in zip(route_ids, routes, checkpoints):
        assessed = assess(route_checkpoints, forecast, request.load_lb)
        summary = summarize([(c.segment_miles, risk) for c, _, risk in assessed])
        options.append(RouteOption(route_id, route.duration_s, summary))
        route_jsons.append(route_json(route_id, route, summary, assessed))

    recommendation = recommend(options)
    heatmap = build_heatmap(grid, forecast, request.departure, request.load_lb)
    return {
        "origin": place_json(origin),
        "destination": place_json(destination),
        "recommended_route_id": recommendation.route_id,
        "recommendation_reason": recommendation.reason,
        "routes": route_jsons,
        "heatmap": {
            "start": iso(request.departure),
            "points": [heatmap_point_json(point) for point in heatmap],
        },
    }


def checkpoints_for(route: HereRoute, request: PlanRequest) -> list[Checkpoint]:
    elapsed = elapsed_seconds(route.points, route.span_offsets, route.span_durations)
    return sample_checkpoints(
        route.points, elapsed, request.departure, request.interval_mi
    )


def assess(
    checkpoints: list[Checkpoint], forecast: Forecast, load_lb: float
) -> list[Assessed]:
    assessed: list[Assessed] = []
    for checkpoint in checkpoints:
        weather = forecast.at((checkpoint.lat, checkpoint.lon), checkpoint.eta)
        risk = checkpoint_risk(weather.risk_input(), load_lb)
        assessed.append((checkpoint, weather, risk))
    return assessed


def thin_line(points: list[Point], min_miles: float) -> list[Point]:
    if len(points) <= 2:
        return points
    kept = [points[0]]
    for point in points[1:-1]:
        if haversine_miles(kept[-1], point) >= min_miles:
            kept.append(point)
    kept.append(points[-1])
    return kept


def iso(time: datetime) -> str:
    return time.isoformat(timespec="seconds")


def round_to_minute(time: datetime) -> datetime:
    return (time + timedelta(seconds=30)).replace(second=0, microsecond=0)


def place_json(place: Place) -> dict[str, Any]:
    return {"label": place.label, "lat": place.lat, "lon": place.lon}


def route_json(
    route_id: str,
    route: HereRoute,
    summary: RouteSummary,
    assessed: list[Assessed],
) -> dict[str, Any]:
    line = thin_line(route.points, LINE_MIN_MILES)
    miles_by_level = {
        level: round(miles, 1) for level, miles in summary.miles_by_level.items()
    }
    avg_risk = None if summary.avg_risk is None else round(summary.avg_risk, 3)
    return {
        "id": route_id,
        "distance_mi": round(route.distance_m / METERS_PER_MILE, 1),
        "duration_s": round(route.duration_s),
        "geometry": [[round(lon, 5), round(lat, 5)] for lat, lon in line],
        "summary": {
            "miles_by_level": miles_by_level,
            "avg_risk": avg_risk,
            "has_no_travel": summary.has_no_travel,
        },
        "checkpoints": [checkpoint_json(*row) for row in assessed],
    }


def checkpoint_json(
    checkpoint: Checkpoint, weather: HourlyWeather, risk: RiskLevel | None
) -> dict[str, Any]:
    return {
        "mile": round(checkpoint.mile, 1),
        "lat": round(checkpoint.lat, 5),
        "lon": round(checkpoint.lon, 5),
        "eta": iso(round_to_minute(checkpoint.eta)),
        "wind_mph": weather.wind_mph,
        "gust_mph": weather.gust_mph,
        "rain_in_hr": weather.rain_in_hr,
        "snow_in_hr": weather.snow_in_hr,
        "risk": level_key(risk),
    }


def heatmap_point_json(point: HeatmapPoint) -> dict[str, Any]:
    return {
        "lat": point.lat,
        "lon": point.lon,
        "risk": [None if level is None else int(level) for level in point.risk],
    }
