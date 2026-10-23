from datetime import UTC, datetime, timedelta

from django.test import SimpleTestCase

from planner.clients.open_meteo import Forecast, HourlyWeather
from planner.heatmap import HOURS, build_heatmap, corridor_grid
from planner.risk import RiskLevel
from planner.sampling import haversine_miles

DEPARTURE = datetime(2026, 10, 24, 13, 0, tzinfo=UTC)
CALM = HourlyWeather(wind_mph=5, gust_mph=8, rain_in_hr=0, snow_in_hr=0)
STORM = HourlyWeather(wind_mph=50, gust_mph=70, rain_in_hr=0, snow_in_hr=0)


def line(start: tuple[float, float], end: tuple[float, float], steps: int) -> list:
    return [
        (
            start[0] + (end[0] - start[0]) * i / steps,
            start[1] + (end[1] - start[1]) * i / steps,
        )
        for i in range(steps + 1)
    ]


class CorridorGridTests(SimpleTestCase):
    def setUp(self) -> None:
        self.route = line((40.0, -100.0), (40.0, -95.0), steps=20)

    def test_points_stay_near_the_route(self) -> None:
        grid = corridor_grid(self.route)
        self.assertTrue(grid)
        for point in grid:
            nearest = min(haversine_miles(point, anchor) for anchor in self.route)
            self.assertLessEqual(nearest, 50)

    def test_covers_the_route(self) -> None:
        grid = corridor_grid(self.route)
        for anchor in self.route:
            nearest = min(haversine_miles(anchor, point) for point in grid)
            self.assertLess(nearest, 30)

    def test_points_are_on_half_degree_grid(self) -> None:
        for lat, lon in corridor_grid(self.route):
            self.assertEqual((lat * 2) % 1, 0)
            self.assertEqual((lon * 2) % 1, 0)

    def test_long_route_gets_coarser_grid(self) -> None:
        route = line((34.0, -118.0), (40.7, -74.0), steps=200)
        grid = corridor_grid(route, max_points=100)
        self.assertLessEqual(len(grid), 100)
        self.assertGreater(len(grid), 10)

    def test_no_anchors_gives_empty_grid(self) -> None:
        self.assertEqual(corridor_grid([]), [])


class BuildHeatmapTests(SimpleTestCase):
    def setUp(self) -> None:
        self.point = (40.0, -100.0)

    def forecast(self, hours: dict[int, HourlyWeather]) -> Forecast:
        by_hour = {DEPARTURE + timedelta(hours=h): w for h, w in hours.items()}
        return Forecast({self.point: by_hour})

    def test_has_one_value_per_hour(self) -> None:
        forecast = self.forecast({h: CALM for h in range(HOURS)})
        [point] = build_heatmap([self.point], forecast, DEPARTURE, load_lb=20_000)
        self.assertEqual(HOURS, 49)
        self.assertEqual(len(point.risk), 49)
        self.assertEqual(set(point.risk), {RiskLevel.LOW})
        self.assertEqual((point.lat, point.lon), self.point)

    def test_hour_index_matches_forecast_time(self) -> None:
        forecast = self.forecast({h: CALM for h in range(HOURS)} | {5: STORM})
        [point] = build_heatmap([self.point], forecast, DEPARTURE, load_lb=20_000)
        self.assertEqual(point.risk[5], RiskLevel.SEVERE)
        self.assertEqual(point.risk[4], RiskLevel.LOW)

    def test_load_rules_apply(self) -> None:
        forecast = self.forecast({0: STORM})
        [point] = build_heatmap([self.point], forecast, DEPARTURE, load_lb=35_000)
        self.assertEqual(point.risk[0], RiskLevel.NO_TRAVEL)

    def test_missing_hours_are_unknown(self) -> None:
        forecast = self.forecast({0: CALM})
        [point] = build_heatmap([self.point], forecast, DEPARTURE, load_lb=20_000)
        self.assertEqual(point.risk[0], RiskLevel.LOW)
        self.assertEqual(point.risk[1:], [None] * 48)

    def test_departure_between_hours_uses_nearest_hour(self) -> None:
        forecast = self.forecast({0: CALM, 1: STORM})
        departure = DEPARTURE + timedelta(minutes=40)
        [point] = build_heatmap([self.point], forecast, departure, load_lb=20_000)
        self.assertEqual(point.risk[0], RiskLevel.SEVERE)
