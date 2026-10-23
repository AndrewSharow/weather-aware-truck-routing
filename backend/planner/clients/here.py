import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import flexpolyline
import requests
from django.conf import settings

from planner.errors import PlannerError
from planner.sampling import Point

logger = logging.getLogger(__name__)

GEOCODE_URL = "https://geocode.search.hereapi.com/v1/geocode"
ROUTES_URL = "https://router.hereapi.com/v8/routes"
TIMEOUT_S = 20
MIN_QUERY_SCORE = 0.7
EMPTY_TRUCK_LB = 35_000
KG_PER_LB = 0.45359237


@dataclass(frozen=True)
class Place:
    label: str
    lat: float
    lon: float


@dataclass(frozen=True)
class HereRoute:
    points: list[Point]
    span_offsets: list[int]
    span_durations: list[float]
    distance_m: float
    duration_s: float


def gross_weight_kg(load_lb: float) -> int:
    return round((load_lb + EMPTY_TRUCK_LB) * KG_PER_LB)


def geocode(query: str) -> Place:
    data = get_json(GEOCODE_URL, {"q": query, "in": "countryCode:USA", "limit": 1})
    items = [
        item
        for item in data.get("items", [])
        if item.get("scoring", {}).get("queryScore", 0) >= MIN_QUERY_SCORE
    ]
    if not items:
        raise PlannerError("place_not_found", f'Place not found: "{query}"', 404)

    item = items[0]
    return Place(
        label=item["address"]["label"],
        lat=item["position"]["lat"],
        lon=item["position"]["lng"],
    )


def truck_routes(
    origin: Place, destination: Place, departure: datetime, load_lb: float
) -> list[HereRoute]:
    data = get_json(
        ROUTES_URL,
        {
            "transportMode": "truck",
            "origin": f"{origin.lat},{origin.lon}",
            "destination": f"{destination.lat},{destination.lon}",
            "departureTime": departure.isoformat(),
            "vehicle[grossWeight]": gross_weight_kg(load_lb),
            "alternatives": 2,
            "return": "polyline,summary",
            "spans": "duration,functionalClass",
        },
    )
    routes = [parse_route(route) for route in data.get("routes", [])]
    if not routes:
        message = "No truck route found between these places."
        raise PlannerError("no_route", message, 404)
    return routes


def parse_route(route: dict[str, Any]) -> HereRoute:
    points: list[Point] = []
    offsets: list[int] = []
    durations: list[float] = []
    distance_m = 0.0
    duration_s = 0.0

    for section in route["sections"]:
        base = len(points)
        decoded = flexpolyline.decode(section["polyline"])
        points.extend((lat, lon) for lat, lon, *_ in decoded)
        for span in section["spans"]:
            offsets.append(base + span["offset"])
            durations.append(span["duration"])
        distance_m += section["summary"]["length"]
        duration_s += section["summary"]["duration"]

    return HereRoute(points, offsets, durations, distance_m, duration_s)


def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.get(
            url, params={**params, "apiKey": settings.HERE_API_KEY}, timeout=TIMEOUT_S
        )
    except requests.RequestException as error:
        logger.warning("HERE request failed: %s", type(error).__name__)
        raise routing_unavailable() from None
    if response.status_code != 200:
        logger.warning("HERE returned status %s", response.status_code)
        raise routing_unavailable()
    return response.json()


def routing_unavailable() -> PlannerError:
    return PlannerError(
        "routing_unavailable", "Routing service is unavailable. Try again later.", 502
    )
