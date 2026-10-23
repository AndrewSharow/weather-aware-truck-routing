from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil, floor

from planner.clients.open_meteo import Forecast
from planner.risk import RiskLevel, checkpoint_risk
from planner.sampling import Point, haversine_miles

HOURS = 49
GRID_STEP_DEG = 0.5
CORRIDOR_MILES = 50
PADDING_DEG = 1.0
MAX_POINTS = 250


@dataclass(frozen=True)
class HeatmapPoint:
    lat: float
    lon: float
    risk: list[RiskLevel | None]


def corridor_grid(anchors: list[Point], max_points: int = MAX_POINTS) -> list[Point]:
    step = GRID_STEP_DEG
    while True:
        grid = grid_near(anchors, step)
        if len(grid) <= max_points:
            return grid
        step *= 2


def grid_near(anchors: list[Point], step: float) -> list[Point]:
    if not anchors:
        return []
    lats = [lat for lat, _ in anchors]
    lons = [lon for _, lon in anchors]
    grid = [
        (lat, lon)
        for lat in steps(min(lats) - PADDING_DEG, max(lats) + PADDING_DEG, step)
        for lon in steps(min(lons) - PADDING_DEG, max(lons) + PADDING_DEG, step)
    ]
    return [
        point
        for point in grid
        if any(haversine_miles(point, anchor) <= CORRIDOR_MILES for anchor in anchors)
    ]


def steps(low: float, high: float, step: float) -> list[float]:
    return [i * step for i in range(ceil(low / step), floor(high / step) + 1)]


def build_heatmap(
    grid: list[Point], forecast: Forecast, departure: datetime, load_lb: float
) -> list[HeatmapPoint]:
    times = [departure + timedelta(hours=hour) for hour in range(HOURS)]
    return [
        HeatmapPoint(
            lat=point[0],
            lon=point[1],
            risk=[
                checkpoint_risk(forecast.at(point, time).risk_input(), load_lb)
                for time in times
            ],
        )
        for point in grid
    ]
