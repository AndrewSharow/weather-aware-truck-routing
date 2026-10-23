import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from planner.clients.here import Place, geocode, gross_weight_kg, truck_routes
from planner.errors import PlannerError

FIXTURES = Path(__file__).parent / "fixtures"
API_KEY = "secret-test-key"
DALLAS = Place(label="Dallas, TX, United States", lat=32.7767, lon=-96.797)
HOUSTON = Place(label="Houston, TX, United States", lat=29.7604, lon=-95.3698)
DEPARTURE = datetime(2026, 10, 24, 13, 0, tzinfo=UTC)


def fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def response(body: dict[str, Any], status: int = 200) -> Mock:
    return Mock(status_code=status, json=Mock(return_value=body))


@override_settings(HERE_API_KEY=API_KEY)
@patch("planner.clients.here.requests.get")
class GeocodeTests(SimpleTestCase):
    def test_returns_label_and_position(self, get: Mock) -> None:
        get.return_value = response(fixture("here_geocode_dallas"))
        place = geocode("Dallas, TX")
        self.assertEqual(place.label, "Dallas, TX, United States")
        self.assertAlmostEqual(place.lat, 32.78, places=1)
        self.assertAlmostEqual(place.lon, -96.80, places=1)

    def test_searches_usa_only(self, get: Mock) -> None:
        get.return_value = response(fixture("here_geocode_dallas"))
        geocode("Dallas, TX")
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["in"], "countryCode:USA")
        self.assertEqual(params["q"], "Dallas, TX")

    def test_no_results_is_not_found(self, get: Mock) -> None:
        get.return_value = response(fixture("here_geocode_empty"))
        with self.assertRaises(PlannerError) as error:
            geocode("asdfgh")
        self.assertEqual(error.exception.code, "place_not_found")
        self.assertEqual(error.exception.status, 404)
        self.assertIn("asdfgh", error.exception.message)

    def test_weak_match_is_not_found(self, get: Mock) -> None:
        get.return_value = response(fixture("here_geocode_low_score"))
        with self.assertRaises(PlannerError) as error:
            geocode("zzzqqq nowhere 12345")
        self.assertEqual(error.exception.code, "place_not_found")


@override_settings(HERE_API_KEY=API_KEY)
@patch("planner.clients.here.requests.get")
class TruckRoutesTests(SimpleTestCase):
    def test_parses_three_routes(self, get: Mock) -> None:
        get.return_value = response(fixture("here_routes_dallas_houston"))
        routes = truck_routes(DALLAS, HOUSTON, DEPARTURE, load_lb=42_000)
        self.assertEqual(len(routes), 3)

    def test_route_geometry_and_timing(self, get: Mock) -> None:
        get.return_value = response(fixture("here_routes_dallas_houston"))
        route = truck_routes(DALLAS, HOUSTON, DEPARTURE, load_lb=42_000)[0]
        self.assertAlmostEqual(route.points[0][0], DALLAS.lat, places=2)
        self.assertAlmostEqual(route.points[-1][0], HOUSTON.lat, places=2)
        self.assertEqual(route.span_offsets, sorted(route.span_offsets))
        self.assertEqual(route.span_offsets[0], 0)
        self.assertEqual(sum(route.span_durations), route.duration_s)
        self.assertEqual(route.distance_m, 384_651)

    def test_sends_truck_request(self, get: Mock) -> None:
        get.return_value = response(fixture("here_routes_dallas_houston"))
        truck_routes(DALLAS, HOUSTON, DEPARTURE, load_lb=42_000)
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["transportMode"], "truck")
        self.assertEqual(params["alternatives"], 2)
        self.assertEqual(params["vehicle[grossWeight]"], gross_weight_kg(42_000))
        self.assertEqual(params["origin"], "32.7767,-96.797")
        self.assertEqual(params["departureTime"], "2026-10-24T13:00:00+00:00")

    def test_no_routes(self, get: Mock) -> None:
        get.return_value = response({"routes": []})
        with self.assertRaises(PlannerError) as error:
            truck_routes(DALLAS, HOUSTON, DEPARTURE, load_lb=42_000)
        self.assertEqual(error.exception.code, "no_route")
        self.assertEqual(error.exception.status, 404)


@override_settings(HERE_API_KEY=API_KEY)
@patch("planner.clients.here.requests.get")
class FailureTests(SimpleTestCase):
    def assert_unavailable(self) -> str:
        with self.assertLogs("planner.clients.here", "WARNING") as logs:
            with self.assertRaises(PlannerError) as error:
                geocode("Dallas, TX")
        self.assertEqual(error.exception.code, "routing_unavailable")
        self.assertEqual(error.exception.status, 502)
        self.assertNotIn(API_KEY, error.exception.message)
        self.assertNotIn(API_KEY, "".join(logs.output))
        return logs.output[0]

    def test_timeout(self, get: Mock) -> None:
        get.side_effect = requests.Timeout(f"timed out apiKey={API_KEY}")
        self.assertIn("Timeout", self.assert_unavailable())

    def test_connection_error(self, get: Mock) -> None:
        get.side_effect = requests.ConnectionError(f"failed apiKey={API_KEY}")
        self.assertIn("ConnectionError", self.assert_unavailable())

    def test_server_error(self, get: Mock) -> None:
        get.return_value = response({"error": "boom"}, status=500)
        self.assertIn("500", self.assert_unavailable())

    def test_unauthorized(self, get: Mock) -> None:
        get.return_value = response({"error": "Unauthorized"}, status=401)
        self.assertIn("401", self.assert_unavailable())


class GrossWeightTests(SimpleTestCase):
    def test_adds_empty_truck_and_converts_to_kg(self) -> None:
        cases = [(0, 15_876), (42_000, 34_927), (45_000, 36_287)]
        for load_lb, expected_kg in cases:
            with self.subTest(load_lb=load_lb):
                self.assertEqual(gross_weight_kg(load_lb), expected_kg)
