from collections.abc import Callable
from dataclasses import dataclass
from math import inf

from planner.risk import RiskLevel

LEVEL_KEYS = ["low", "moderate", "high", "severe", "no_travel", "unknown"]


@dataclass(frozen=True)
class RouteSummary:
    miles_by_level: dict[str, float]
    avg_risk: float | None
    has_no_travel: bool


@dataclass(frozen=True)
class RouteOption:
    id: str
    duration_s: float
    summary: RouteSummary


@dataclass(frozen=True)
class Recommendation:
    route_id: str
    reason: str


def level_key(level: RiskLevel | None) -> str:
    return "unknown" if level is None else level.name.lower()


def summarize(segments: list[tuple[float, RiskLevel | None]]) -> RouteSummary:
    miles_by_level = {key: 0.0 for key in LEVEL_KEYS}
    for miles, level in segments:
        miles_by_level[level_key(level)] += miles

    known = [(miles, level) for miles, level in segments if level is not None]
    known_miles = sum(miles for miles, _ in known)
    avg_risk = (
        sum(miles * level for miles, level in known) / known_miles
        if known_miles
        else None
    )
    return RouteSummary(
        miles_by_level=miles_by_level,
        avg_risk=avg_risk,
        has_no_travel=miles_by_level["no_travel"] > 0,
    )


def miles_at(level: str) -> Callable[[RouteOption], float]:
    return lambda route: round(route.summary.miles_by_level[level], 1)


def avg_risk(route: RouteOption) -> float:
    value = route.summary.avg_risk
    return inf if value is None else round(value, 3)


def duration(route: RouteOption) -> float:
    return route.duration_s


CRITERIA: list[tuple[str, Callable[[RouteOption], float]]] = [
    ("Fewest No Travel miles", miles_at("no_travel")),
    ("Fewest Severe miles", miles_at("severe")),
    ("Fewest High miles", miles_at("high")),
    ("Lowest average risk", avg_risk),
    ("Shortest travel time", duration),
]


def ranking_key(route: RouteOption) -> tuple[float, ...]:
    return tuple(value(route) for _, value in CRITERIA)


def recommend(routes: list[RouteOption]) -> Recommendation:
    if not routes:
        raise ValueError("No routes to compare")

    ranked = sorted(routes, key=ranking_key)
    best = ranked[0]
    if len(ranked) == 1:
        return Recommendation(best.id, "Only route available")
    return Recommendation(best.id, reason(best, ranked[1]))


def reason(best: RouteOption, runner_up: RouteOption) -> str:
    for text, value in CRITERIA:
        if value(best) < value(runner_up):
            if text == "Fewest No Travel miles" and not best.summary.has_no_travel:
                return "Avoids No Travel"
            return text
    return "Equal on all criteria"
