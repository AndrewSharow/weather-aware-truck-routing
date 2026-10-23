from dataclasses import dataclass
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_MILES = 3958.8
MIN_LAST_SEGMENT_MILES = 0.01

Point = tuple[float, float]


@dataclass(frozen=True)
class Checkpoint:
    mile: float
    lat: float
    lon: float
    eta: datetime
    segment_miles: float


def haversine_miles(a: Point, b: Point) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (*a, *b))
    lat_term = sin((lat2 - lat1) / 2) ** 2
    lon_term = cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * asin(sqrt(lat_term + lon_term))


def interpolate(a: Point, b: Point, ratio: float) -> Point:
    return (a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio)


def elapsed_seconds(
    points: list[Point], span_offsets: list[int], span_durations: list[float]
) -> list[float]:
    elapsed = [0.0] * len(points)
    span_ends = [*span_offsets[1:], len(points) - 1]
    clock = 0.0
    for start, end, duration in zip(span_offsets, span_ends, span_durations):
        lengths = [haversine_miles(points[i], points[i + 1]) for i in range(start, end)]
        span_miles = sum(lengths)
        for i, length in enumerate(lengths, start=start):
            share = length / span_miles if span_miles else 0
            elapsed[i + 1] = elapsed[i] + duration * share
        clock += duration
        elapsed[end] = clock
    return elapsed


def sample_checkpoints(
    points: list[Point],
    elapsed: list[float],
    departure: datetime,
    interval_mi: float,
) -> list[Checkpoint]:
    checkpoints: list[Checkpoint] = []
    target = interval_mi
    travelled = 0.0

    for i in range(len(points) - 1):
        length = haversine_miles(points[i], points[i + 1])
        while length and target < travelled + length:
            ratio = (target - travelled) / length
            lat, lon = interpolate(points[i], points[i + 1], ratio)
            seconds = elapsed[i] + (elapsed[i + 1] - elapsed[i]) * ratio
            eta = departure + timedelta(seconds=seconds)
            checkpoints.append(Checkpoint(target, lat, lon, eta, interval_mi))
            target += interval_mi
        travelled += length

    last_mile = checkpoints[-1].mile if checkpoints else 0.0
    remainder = travelled - last_mile
    if remainder >= MIN_LAST_SEGMENT_MILES or not checkpoints:
        lat, lon = points[-1]
        eta = departure + timedelta(seconds=elapsed[-1])
        checkpoints.append(Checkpoint(travelled, lat, lon, eta, remainder))
    return checkpoints
