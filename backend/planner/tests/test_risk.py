from django.test import SimpleTestCase

from planner.risk import (
    RiskLevel,
    Weather,
    checkpoint_risk,
    rain_level,
    snow_level,
    wind_level,
    wind_level_with_load,
)

LOW = RiskLevel.LOW
MODERATE = RiskLevel.MODERATE
HIGH = RiskLevel.HIGH
SEVERE = RiskLevel.SEVERE
NO_TRAVEL = RiskLevel.NO_TRAVEL


class WindLevelTests(SimpleTestCase):
    def test_thresholds(self) -> None:
        cases = [
            (0, LOW),
            (24.9, LOW),
            (25, MODERATE),
            (34.9, MODERATE),
            (35, HIGH),
            (44.9, HIGH),
            (45, SEVERE),
            (54.9, SEVERE),
            (55, NO_TRAVEL),
            (80, NO_TRAVEL),
        ]
        for mph, expected in cases:
            with self.subTest(mph=mph):
                self.assertEqual(wind_level(mph), expected)


class RainLevelTests(SimpleTestCase):
    def test_thresholds(self) -> None:
        cases = [
            (0, LOW),
            (0.09, LOW),
            (0.10, MODERATE),
            (0.24, MODERATE),
            (0.25, HIGH),
            (0.49, HIGH),
            (0.50, SEVERE),
            (1.00, SEVERE),
            (1.01, NO_TRAVEL),
        ]
        for in_hr, expected in cases:
            with self.subTest(in_hr=in_hr):
                self.assertEqual(rain_level(in_hr), expected)


class SnowLevelTests(SimpleTestCase):
    def test_thresholds(self) -> None:
        cases = [
            (0, LOW),
            (0.49, LOW),
            (0.5, MODERATE),
            (0.99, MODERATE),
            (1.0, HIGH),
            (1.99, HIGH),
            (2.0, SEVERE),
            (3.0, SEVERE),
            (3.01, NO_TRAVEL),
        ]
        for in_hr, expected in cases:
            with self.subTest(in_hr=in_hr):
                self.assertEqual(snow_level(in_hr), expected)


class WindWithLoadTests(SimpleTestCase):
    def test_load_rules(self) -> None:
        cases = [
            (50, 30_000, SEVERE),
            (50, 30_001, NO_TRAVEL),
            (45, 45_000, NO_TRAVEL),
            (40, 40_000, HIGH),
            (40, 40_001, SEVERE),
            (35, 45_000, SEVERE),
            (60, 0, NO_TRAVEL),
            (30, 45_000, MODERATE),
            (10, 45_000, LOW),
        ]
        for mph, load_lb, expected in cases:
            with self.subTest(mph=mph, load_lb=load_lb):
                self.assertEqual(wind_level_with_load(mph, load_lb), expected)


class CheckpointRiskTests(SimpleTestCase):
    def test_all_low(self) -> None:
        weather = Weather(wind_mph=10, rain_in_hr=0, snow_in_hr=0)
        self.assertEqual(checkpoint_risk(weather, load_lb=20_000), LOW)

    def test_worst_condition_wins(self) -> None:
        weather = Weather(wind_mph=30, rain_in_hr=0.3, snow_in_hr=0)
        self.assertEqual(checkpoint_risk(weather, load_lb=20_000), HIGH)

    def test_load_raises_wind_above_rain(self) -> None:
        weather = Weather(wind_mph=46, rain_in_hr=0.3, snow_in_hr=0)
        self.assertEqual(checkpoint_risk(weather, load_lb=35_000), NO_TRAVEL)

    def test_rain_beats_load_raised_wind(self) -> None:
        weather = Weather(wind_mph=40, rain_in_hr=1.5, snow_in_hr=0)
        self.assertEqual(checkpoint_risk(weather, load_lb=42_000), NO_TRAVEL)

    def test_missing_value_is_unknown(self) -> None:
        cases = [
            Weather(wind_mph=None, rain_in_hr=0, snow_in_hr=0),
            Weather(wind_mph=10, rain_in_hr=None, snow_in_hr=0),
            Weather(wind_mph=10, rain_in_hr=0, snow_in_hr=None),
        ]
        for weather in cases:
            with self.subTest(weather=weather):
                self.assertIsNone(checkpoint_risk(weather, load_lb=20_000))
