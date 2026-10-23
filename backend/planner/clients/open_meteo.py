from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import requests
from django.core.cache import cache

from planner.errors import PlannerError
from planner.risk import Weather
from planner.sampling import Point

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = ["wind_speed_10m", "wind_gusts_10m", "rain", "showers", "snowfall"]
TIMEOUT_S = 20
BATCH_SIZE = 100
FORECAST_HORIZON = timedelta(days=15)
CACHE_SECONDS = 3600
HOUR_FORMAT = "%Y-%m-%dT%H:%M"


@dataclass(frozen=True)
class HourlyWeather:
    wind_mph: float | None
    gust_mph: float | None
    rain_in_hr: float | None
    snow_in_hr: float | None

    def risk_input(self) -> Weather:
        return Weather(self.wind_mph, self.rain_in_hr, self.snow_in_hr)


MISSING = HourlyWeather(None, None, None, None)


@dataclass(frozen=True)
class Forecast:
    by_cell: dict[Point, dict[datetime, HourlyWeather]] = field(default_factory=dict)

    def at(self, point: Point, time: datetime) -> HourlyWeather:
        return self.by_cell.get(grid_cell(point), {}).get(nearest_hour(time), MISSING)


def grid_cell(point: Point) -> Point:
    return (round(point[0], 1), round(point[1], 1))


def floor_hour(time: datetime) -> datetime:
    return time.replace(minute=0, second=0, microsecond=0)


def nearest_hour(time: datetime) -> datetime:
    return floor_hour(time + timedelta(minutes=30))


def fetch_forecast(
    points: list[Point], start: datetime, end: datetime, now: datetime | None = None
) -> Forecast:
    now = now or datetime.now(UTC)
    first_hour = floor_hour(start).replace(hour=0)
    last_hour = min(
        nearest_hour(end).replace(hour=23), floor_hour(now + FORECAST_HORIZON)
    )
    if first_hour > last_hour:
        return Forecast()

    cells = list(dict.fromkeys(grid_cell(point) for point in points))
    keys = {cell: cache_key(cell, first_hour, last_hour) for cell in cells}
    cached = cache.get_many(keys.values())
    by_cell = {cell: cached[key] for cell, key in keys.items() if key in cached}

    missing = [cell for cell in cells if cell not in by_cell]
    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i : i + BATCH_SIZE]
        locations = fetch_batch(batch, first_hour, last_hour)
        for cell, location in zip(batch, locations):
            by_cell[cell] = parse_hourly(location["hourly"])
            cache.set(keys[cell], by_cell[cell], CACHE_SECONDS)
    return Forecast(by_cell)


def cache_key(cell: Point, first_hour: datetime, last_hour: datetime) -> str:
    return f"open-meteo:{cell[0]}:{cell[1]}:{first_hour:%Y%m%d%H}:{last_hour:%Y%m%d%H}"


def fetch_batch(
    cells: list[Point], first_hour: datetime, last_hour: datetime
) -> list[dict[str, Any]]:
    params = {
        "latitude": ",".join(str(lat) for lat, _ in cells),
        "longitude": ",".join(str(lon) for _, lon in cells),
        "hourly": ",".join(HOURLY_FIELDS),
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "GMT",
        "start_hour": first_hour.strftime(HOUR_FORMAT),
        "end_hour": last_hour.strftime(HOUR_FORMAT),
    }
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=TIMEOUT_S)
    except requests.RequestException:
        raise weather_unavailable() from None
    if response.status_code != 200:
        raise weather_unavailable()

    data = response.json()
    locations = data if isinstance(data, list) else [data]
    if len(locations) != len(cells):
        raise weather_unavailable()
    return locations


def parse_hourly(hourly: dict[str, list[Any]]) -> dict[datetime, HourlyWeather]:
    times = hourly["time"]
    values = {name: hourly.get(name, [None] * len(times)) for name in HOURLY_FIELDS}
    return {
        datetime.fromisoformat(time).replace(tzinfo=UTC): HourlyWeather(
            wind_mph=values["wind_speed_10m"][i],
            gust_mph=values["wind_gusts_10m"][i],
            rain_in_hr=add(values["rain"][i], values["showers"][i]),
            snow_in_hr=values["snowfall"][i],
        )
        for i, time in enumerate(times)
    }


def add(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else a + b


def weather_unavailable() -> PlannerError:
    return PlannerError(
        "weather_unavailable", "Weather service is unavailable. Try again later.", 502
    )
