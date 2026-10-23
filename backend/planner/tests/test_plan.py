from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from planner.clients.here import HereRoute, Place
from planner.clients.open_meteo import HourlyWeather
from planner.heatmap import HOURS
from planner.plan import plan_trip, thin_line
from planner.sampling import Point, haversine_miles
from planner.serializers import PlanRequest

DEPARTURE = datetime(2026, 10, 24, 13, 0, tzinfo=UTC)
ORIGIN = Place("Origin, KS, United States", 38.0, -98.0)
DESTINATION = Place("Destination, NE, United States", 39.45, -98.0)
CALM = HourlyWeather(wind_mph=5, gust_mph=8, rain_in_hr=0, snow_in_hr=0)
WINDY = HourlyWeather(wind_mph=40, gust_mph=55, rain_in_hr=0, snow_in_hr=0)
MISSING = HourlyWeather(None, None, None, None)


DEGREES_PER_MILE = 1 / haversine_miles((0, 0), (1, 0))


def north_route(lon: float, hours: float) -> HereRoute:
    points = [(38.0 + i * DEGREES_PER_MILE, lon) for i in range(101)]
    return HereRoute(
        points=points,
        span_offsets=[0],
        span_durations=[hours * 3600],
        distance_m=160_934,
        duration_s=hours * 3600,
    )


class FakeForecast:
    def __init__(self, weather_by_lon: dict[float, HourlyWeather]) -> None:
        self.weather_by_lon = weather_by_lon

    def at(self, point: Point, time: datetime) -> HourlyWeather:
        return self.weather_by_lon.get(round(point[1], 1), CALM)


def request(**overrides: Any) -> PlanRequest:
    values: dict[str, Any] = {
        "origin": "Origin, KS",
        "destination": "Destination, NE",
        "departure": DEPARTURE,
        "load_lb": 42_000,
        "interval_mi": 25,
        **overrides,
    }
    return PlanRequest(**values)


@patch("planner.plan.fetch_forecast")
@patch("planner.plan.truck_routes")
@patch("planner.plan.geocode")
class PlanTripTests(SimpleTestCase):
    def run_plan(
        self,
        geocode: Mock,
        truck_routes: Mock,
        fetch_forecast: Mock,
        weather_by_lon: dict[float, HourlyWeather] | None = None,
    ) -> dict[str, Any]:
        geocode.side_effect = [ORIGIN, DESTINATION]
        truck_routes.return_value = [
            north_route(-98.0, hours=2),
            north_route(-97.0, hours=3),
        ]
        fetch_forecast.return_value = FakeForecast(weather_by_lon or {})
        return plan_trip(request())

    def test_places_and_route_ids(self, *mocks: Mock) -> None:
        result = self.run_plan(*mocks)
        self.assertEqual(result["origin"]["label"], ORIGIN.label)
        self.assertEqual(result["destination"]["lat"], DESTINATION.lat)
        self.assertEqual([route["id"] for route in result["routes"]], ["A", "B"])

    def test_route_fields(self, *mocks: Mock) -> None:
        route = self.run_plan(*mocks)["routes"][0]
        self.assertAlmostEqual(route["distance_mi"], 100.0, places=1)
        self.assertEqual(route["duration_s"], 7200)
        self.assertEqual(route["geometry"][0], [-98.0, 38.0])

    def test_checkpoints_every_interval_with_eta(self, *mocks: Mock) -> None:
        checkpoints = self.run_plan(*mocks)["routes"][0]["checkpoints"]
        self.assertEqual([round(c["mile"]) for c in checkpoints], [25, 50, 75, 100])
        self.assertEqual(checkpoints[0]["eta"], "2026-10-24T13:30:00+00:00")
        self.assertEqual(checkpoints[0]["risk"], "low")
        self.assertEqual(checkpoints[0]["wind_mph"], 5)
        self.assertEqual(checkpoints[0]["gust_mph"], 8)

    def test_load_rules_and_recommendation(self, *mocks: Mock) -> None:
        result = self.run_plan(*mocks, weather_by_lon={-98.0: WINDY})
        route_a = result["routes"][0]
        self.assertEqual({c["risk"] for c in route_a["checkpoints"]}, {"severe"})
        self.assertEqual(route_a["summary"]["miles_by_level"]["severe"], 100.0)
        self.assertEqual(result["recommended_route_id"], "B")
        self.assertEqual(result["recommendation_reason"], "Fewest Severe miles")

    def test_shortest_route_wins_when_weather_is_equal(self, *mocks: Mock) -> None:
        result = self.run_plan(*mocks)
        self.assertEqual(result["recommended_route_id"], "A")
        self.assertEqual(result["recommendation_reason"], "Shortest travel time")

    def test_missing_weather_is_unknown(self, *mocks: Mock) -> None:
        result = self.run_plan(*mocks, weather_by_lon={-98.0: MISSING})
        route_a = result["routes"][0]
        self.assertEqual({c["risk"] for c in route_a["checkpoints"]}, {"unknown"})
        self.assertIsNone(route_a["summary"]["avg_risk"])
        self.assertIsNone(route_a["checkpoints"][0]["wind_mph"])

    def test_heatmap_has_49_hours(self, *mocks: Mock) -> None:
        heatmap = self.run_plan(*mocks)["heatmap"]
        self.assertEqual(heatmap["start"], "2026-10-24T13:00:00+00:00")
        self.assertTrue(heatmap["points"])
        for point in heatmap["points"]:
            self.assertEqual(len(point["risk"]), HOURS)
            self.assertEqual(set(point["risk"]), {0})

    def test_forecast_window_covers_trip_and_heatmap(self, *mocks: Mock) -> None:
        self.run_plan(*mocks)
        fetch_forecast = mocks[2]
        points, start, end = fetch_forecast.call_args.args
        self.assertEqual(start, DEPARTURE)
        self.assertEqual(end, DEPARTURE + timedelta(hours=HOURS - 1))
        self.assertGreater(len(points), 8)

    def test_truck_routes_get_places_and_load(self, *mocks: Mock) -> None:
        self.run_plan(*mocks)
        truck_routes = mocks[1]
        truck_routes.assert_called_once_with(ORIGIN, DESTINATION, DEPARTURE, 42_000)


class ThinLineTests(SimpleTestCase):
    def test_keeps_ends_and_drops_close_points(self) -> None:
        points = [(38.0 + i * 0.0001, -98.0) for i in range(1001)]
        thinned = thin_line(points, min_miles=0.5)
        self.assertEqual(thinned[0], points[0])
        self.assertEqual(thinned[-1], points[-1])
        self.assertLess(len(thinned), 20)
        for a, b in zip(thinned, thinned[1:-1]):
            self.assertGreaterEqual(haversine_miles(a, b), 0.5)

    def test_short_line_is_unchanged(self) -> None:
        points = [(38.0, -98.0), (38.1, -98.0)]
        self.assertEqual(thin_line(points, min_miles=0.5), points)
