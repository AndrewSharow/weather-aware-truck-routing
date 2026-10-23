from datetime import timedelta
from typing import Any

from django.test import SimpleTestCase
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from planner.serializers import PlanRequestSerializer, parse_plan_request


def body(**overrides: Any) -> dict[str, Any]:
    departure = timezone.now() + timedelta(hours=2)
    return {
        "origin": "Chicago, IL",
        "destination": "Denver, CO",
        "departure": departure.isoformat(),
        "load_lb": 42_000,
        "interval_mi": 25,
        **overrides,
    }


class PlanRequestSerializerTests(SimpleTestCase):
    def errors(self, data: dict[str, Any]) -> dict[str, Any]:
        serializer = PlanRequestSerializer(data=data)
        serializer.is_valid()
        return dict(serializer.errors)

    def test_valid_body(self) -> None:
        request = parse_plan_request(body())
        self.assertEqual(request.origin, "Chicago, IL")
        self.assertEqual(request.load_lb, 42_000)
        self.assertEqual(request.interval_mi, 25)
        self.assertIsNotNone(request.departure.tzinfo)

    def test_parse_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            parse_plan_request(body(load_lb=-5))

    def test_every_field_is_required(self) -> None:
        for field in ("origin", "destination", "departure", "load_lb", "interval_mi"):
            with self.subTest(field=field):
                data = body()
                del data[field]
                self.assertIn(field, self.errors(data))

    def test_blank_place_is_rejected(self) -> None:
        self.assertIn("origin", self.errors(body(origin="   ")))

    def test_same_origin_and_destination(self) -> None:
        errors = self.errors(body(destination=" chicago, il "))
        self.assertIn("destination", errors)

    def test_load_limits(self) -> None:
        cases = [(0, True), (45_000, True), (-1, False), (45_001, False)]
        for load_lb, valid in cases:
            with self.subTest(load_lb=load_lb):
                errors = self.errors(body(load_lb=load_lb))
                self.assertEqual("load_lb" not in errors, valid)

    def test_interval_choices(self) -> None:
        cases = [(10, True), (25, True), (50, True), (30, False), (0, False)]
        for interval, valid in cases:
            with self.subTest(interval=interval):
                errors = self.errors(body(interval_mi=interval))
                self.assertEqual("interval_mi" not in errors, valid)

    def test_departure_window(self) -> None:
        now = timezone.now()
        cases = [
            (now - timedelta(minutes=2), True),
            (now + timedelta(days=6, hours=23), True),
            (now - timedelta(hours=1), False),
            (now + timedelta(days=7, hours=1), False),
        ]
        for departure, valid in cases:
            with self.subTest(departure=departure):
                errors = self.errors(body(departure=departure.isoformat()))
                self.assertEqual("departure" not in errors, valid)

    def test_bad_departure_format(self) -> None:
        self.assertIn("departure", self.errors(body(departure="tomorrow")))
