import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from planner.clients.open_meteo import (
    HourlyWeather,
    fetch_forecast,
    grid_cell,
    nearest_hour,
)
from planner.errors import PlannerError

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 23, 20, 0, tzinfo=UTC)
START = datetime(2026, 10, 24, 13, 0, tzinfo=UTC)
END = datetime(2026, 10, 24, 15, 0, tzinfo=UTC)
POINTS = [(32.8, -96.8), (31.5, -96.0), (29.8, -95.4)]


def three_points() -> list[dict[str, Any]]:
    return json.loads((FIXTURES / "open_meteo_three_points.json").read_text())


def location(**hourly: list[Any]) -> dict[str, Any]:
    return {"hourly": {"time": ["2026-10-24T13:00"], **hourly}}


def response(body: Any, status: int = 200) -> Mock:
    return Mock(status_code=status, json=Mock(return_value=body))


class HelperTests(SimpleTestCase):
    def test_grid_cell_rounds_to_tenth_of_degree(self) -> None:
        self.assertEqual(grid_cell((32.83, -96.77)), (32.8, -96.8))
        self.assertEqual(grid_cell((29.76, -95.37)), (29.8, -95.4))

    def test_nearest_hour(self) -> None:
        base = datetime(2026, 10, 24, 13, 0, tzinfo=UTC)
        cases = [(0, 13), (29, 13), (30, 14), (59, 14)]
        for minute, hour in cases:
            with self.subTest(minute=minute):
                result = nearest_hour(base + timedelta(minutes=minute))
                self.assertEqual(result, base.replace(hour=hour))


@patch("planner.clients.open_meteo.requests.get")
class FetchForecastTests(SimpleTestCase):
    def setUp(self) -> None:
        cache.clear()

    def fetch(self, points: list[tuple[float, float]] = POINTS) -> Any:
        return fetch_forecast(points, START, END, now=NOW)

    def test_reads_values_for_each_point_and_hour(self, get: Mock) -> None:
        get.return_value = response(three_points())
        forecast = self.fetch()
        expected = three_points()[0]["hourly"]
        weather = forecast.at((32.81, -96.79), START + timedelta(hours=1))
        self.assertEqual(weather.wind_mph, expected["wind_speed_10m"][1])
        self.assertEqual(weather.gust_mph, expected["wind_gusts_10m"][1])
        self.assertEqual(weather.snow_in_hr, expected["snowfall"][1])

    @override_settings(OPEN_METEO_URL="https://proxy.example.workers.dev")
    def test_uses_configured_url(self, get: Mock) -> None:
        get.return_value = response(three_points())
        self.fetch()
        url = get.call_args.args[0]
        self.assertEqual(url, "https://proxy.example.workers.dev/v1/forecast")

    def test_requests_mph_inch_and_utc(self, get: Mock) -> None:
        get.return_value = response(three_points())
        self.fetch()
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["wind_speed_unit"], "mph")
        self.assertEqual(params["precipitation_unit"], "inch")
        self.assertEqual(params["timezone"], "GMT")
        self.assertEqual(params["start_hour"], "2026-10-24T00:00")
        self.assertEqual(params["end_hour"], "2026-10-24T23:00")

    def test_rain_includes_showers(self, get: Mock) -> None:
        body = location(
            wind_speed_10m=[5],
            wind_gusts_10m=[9],
            rain=[0.1],
            showers=[0.2],
            snowfall=[0],
        )
        get.return_value = response(body)
        weather = self.fetch([(32.8, -96.8)]).at((32.8, -96.8), START)
        self.assertAlmostEqual(weather.rain_in_hr or 0, 0.3)

    def test_null_values_are_missing(self, get: Mock) -> None:
        body = location(
            wind_speed_10m=[None],
            wind_gusts_10m=[None],
            rain=[None],
            showers=[0],
            snowfall=[None],
        )
        get.return_value = response(body)
        weather = self.fetch([(32.8, -96.8)]).at((32.8, -96.8), START)
        self.assertEqual(weather, HourlyWeather(None, None, None, None))

    def test_unknown_point_or_hour_is_missing(self, get: Mock) -> None:
        get.return_value = response(three_points())
        forecast = self.fetch()
        missing = HourlyWeather(None, None, None, None)
        self.assertEqual(forecast.at((40.0, -100.0), START), missing)
        self.assertEqual(forecast.at(POINTS[0], START + timedelta(days=1)), missing)

    def test_points_in_same_cell_are_requested_once(self, get: Mock) -> None:
        get.return_value = response(three_points()[0])
        self.fetch([(32.81, -96.79), (32.79, -96.81), (32.8, -96.8)])
        self.assertEqual(get.call_count, 1)
        self.assertEqual(get.call_args.kwargs["params"]["latitude"], "32.8")

    def test_many_points_are_sent_in_batches(self, get: Mock) -> None:
        points = [(30 + i / 10, -96.0) for i in range(150)]
        get.side_effect = [
            response([location()] * 100),
            response([location()] * 50),
        ]
        self.fetch(points)
        self.assertEqual(get.call_count, 2)

    def test_window_past_forecast_horizon_is_cut(self, get: Mock) -> None:
        get.return_value = response(three_points())
        fetch_forecast(POINTS, START, NOW + timedelta(days=30), now=NOW)
        end_hour = get.call_args.kwargs["params"]["end_hour"]
        self.assertEqual(end_hour, "2026-11-07T20:00")

    def test_second_request_uses_cache(self, get: Mock) -> None:
        get.return_value = response(three_points())
        self.fetch()
        forecast = self.fetch()
        self.assertEqual(get.call_count, 1)
        self.assertIsNotNone(forecast.at(POINTS[0], START).wind_mph)

    def test_only_missing_cells_are_fetched(self, get: Mock) -> None:
        get.return_value = response(three_points()[0])
        self.fetch([POINTS[0]])
        get.return_value = response(three_points()[1:])
        forecast = self.fetch()
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args.kwargs["params"]["latitude"], "31.5,29.8")
        self.assertIsNotNone(forecast.at(POINTS[2], START).wind_mph)

    def test_window_fully_past_horizon_skips_request(self, get: Mock) -> None:
        start = NOW + timedelta(days=20)
        forecast = fetch_forecast(POINTS, start, start + timedelta(hours=5), now=NOW)
        get.assert_not_called()
        self.assertIsNone(forecast.at(POINTS[0], start).wind_mph)


@patch("planner.clients.open_meteo.requests.get")
class FailureTests(SimpleTestCase):
    def setUp(self) -> None:
        cache.clear()

    def fetch_error(self) -> tuple[PlannerError, str]:
        with self.assertLogs("planner.clients.open_meteo", "WARNING") as logs:
            with self.assertRaises(PlannerError) as error:
                fetch_forecast(POINTS, START, END, now=NOW)
        self.assertEqual(error.exception.status, 502)
        return error.exception, logs.output[0]

    def assert_unavailable(self, logged: str) -> None:
        error, log = self.fetch_error()
        self.assertEqual(error.code, "weather_unavailable")
        self.assertIn(logged, log)

    def test_timeout(self, get: Mock) -> None:
        get.side_effect = requests.Timeout()
        self.assert_unavailable("Timeout")

    def test_server_error(self, get: Mock) -> None:
        get.return_value = response({"error": True}, status=500)
        self.assert_unavailable("500")

    def test_bad_request(self, get: Mock) -> None:
        get.return_value = response({"error": True, "reason": "out of range"}, 400)
        self.assert_unavailable("400")

    def test_rate_limited(self, get: Mock) -> None:
        get.return_value = response({"error": True}, status=429)
        error, log = self.fetch_error()
        self.assertEqual(error.code, "weather_rate_limited")
        self.assertIn("busy", error.message)
        self.assertIn("429", log)

    def test_wrong_number_of_locations(self, get: Mock) -> None:
        get.return_value = response(three_points()[:2])
        with self.assertRaises(PlannerError) as error:
            fetch_forecast(POINTS, START, END, now=NOW)
        self.assertEqual(error.exception.code, "weather_unavailable")
