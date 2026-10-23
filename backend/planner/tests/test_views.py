from datetime import timedelta
from typing import Any
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from planner.errors import PlannerError


def body(**overrides: Any) -> dict[str, Any]:
    return {
        "origin": "Chicago, IL",
        "destination": "Denver, CO",
        "departure": (timezone.now() + timedelta(hours=2)).isoformat(),
        "load_lb": 42_000,
        "interval_mi": 25,
        **overrides,
    }


@patch("planner.views.plan_trip")
class PlanViewTests(SimpleTestCase):
    def post(self, data: dict[str, Any]) -> Any:
        return self.client.post("/api/plan", data, content_type="application/json")

    def test_returns_plan(self, plan_trip: Mock) -> None:
        plan_trip.return_value = {"routes": [], "recommended_route_id": "A"}
        with self.assertLogs("planner.views", "INFO") as logs:
            response = self.post(body())
        self.assertIn("Chicago, IL -> Denver, CO: 0 routes", logs.output[0])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recommended_route_id"], "A")
        self.assertEqual(plan_trip.call_args.args[0].origin, "Chicago, IL")

    def test_invalid_input(self, plan_trip: Mock) -> None:
        response = self.post(body(load_lb=50_000, interval_mi=30))
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"], "invalid_input")
        self.assertIn("load_lb", data["fields"])
        self.assertIn("interval_mi", data["fields"])
        plan_trip.assert_not_called()

    def test_planner_error(self, plan_trip: Mock) -> None:
        plan_trip.side_effect = PlannerError("place_not_found", "Place not found", 404)
        with self.assertLogs("planner.views", "INFO") as logs:
            response = self.post(body())
        self.assertIn("failed: place_not_found", logs.output[0])
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(), {"error": "place_not_found", "message": "Place not found"}
        )

    def test_only_post_is_allowed(self, plan_trip: Mock) -> None:
        response: Any = self.client.get("/api/plan")
        self.assertEqual(response.status_code, 405)
