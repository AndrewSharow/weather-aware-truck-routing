from dataclasses import dataclass
from enum import IntEnum


class RiskLevel(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4


@dataclass(frozen=True)
class Weather:
    wind_mph: float | None
    rain_in_hr: float | None
    snow_in_hr: float | None


def wind_level(mph: float) -> RiskLevel:
    if mph < 25:
        return RiskLevel.LOW
    if mph < 35:
        return RiskLevel.MODERATE
    if mph < 45:
        return RiskLevel.HIGH
    if mph < 55:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def rain_level(in_hr: float) -> RiskLevel:
    if in_hr < 0.10:
        return RiskLevel.LOW
    if in_hr < 0.25:
        return RiskLevel.MODERATE
    if in_hr < 0.50:
        return RiskLevel.HIGH
    if in_hr <= 1.00:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def snow_level(in_hr: float) -> RiskLevel:
    if in_hr < 0.5:
        return RiskLevel.LOW
    if in_hr < 1.0:
        return RiskLevel.MODERATE
    if in_hr < 2.0:
        return RiskLevel.HIGH
    if in_hr <= 3.0:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def wind_level_with_load(mph: float, load_lb: float) -> RiskLevel:
    level = wind_level(mph)
    if level == RiskLevel.SEVERE and load_lb > 30_000:
        return RiskLevel.NO_TRAVEL
    if level == RiskLevel.HIGH and load_lb > 40_000:
        return RiskLevel.SEVERE
    return level


def checkpoint_risk(weather: Weather, load_lb: float) -> RiskLevel | None:
    wind, rain, snow = weather.wind_mph, weather.rain_in_hr, weather.snow_in_hr
    if wind is None or rain is None or snow is None:
        return None
    return max(wind_level_with_load(wind, load_lb), rain_level(rain), snow_level(snow))
