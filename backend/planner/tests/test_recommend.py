from django.test import SimpleTestCase

from planner.recommend import RouteOption, RouteSummary, recommend, summarize
from planner.risk import RiskLevel

LOW = RiskLevel.LOW
MODERATE = RiskLevel.MODERATE
HIGH = RiskLevel.HIGH
SEVERE = RiskLevel.SEVERE
NO_TRAVEL = RiskLevel.NO_TRAVEL


def route(
    route_id: str,
    duration_s: float = 36_000,
    no_travel: float = 0,
    severe: float = 0,
    high: float = 0,
    avg_risk: float | None = 0.5,
) -> RouteOption:
    summary = RouteSummary(
        miles_by_level={
            "low": 100,
            "moderate": 0,
            "high": high,
            "severe": severe,
            "no_travel": no_travel,
            "unknown": 0,
        },
        avg_risk=avg_risk,
        has_no_travel=no_travel > 0,
    )
    return RouteOption(id=route_id, duration_s=duration_s, summary=summary)


class SummarizeTests(SimpleTestCase):
    def test_miles_per_level(self) -> None:
        summary = summarize([(25, LOW), (25, LOW), (25, HIGH), (10, SEVERE)])
        self.assertEqual(
            summary.miles_by_level,
            {
                "low": 50,
                "moderate": 0,
                "high": 25,
                "severe": 10,
                "no_travel": 0,
                "unknown": 0,
            },
        )
        self.assertFalse(summary.has_no_travel)

    def test_average_is_weighted_by_miles(self) -> None:
        summary = summarize([(30, LOW), (10, SEVERE)])
        self.assertAlmostEqual(summary.avg_risk or 0, 0.75)

    def test_unknown_is_counted_but_not_averaged(self) -> None:
        summary = summarize([(25, HIGH), (25, None)])
        self.assertEqual(summary.miles_by_level["unknown"], 25)
        self.assertAlmostEqual(summary.avg_risk or 0, 2.0)

    def test_all_unknown_has_no_average(self) -> None:
        summary = summarize([(25, None), (25, None)])
        self.assertIsNone(summary.avg_risk)

    def test_no_travel_flag(self) -> None:
        summary = summarize([(25, LOW), (5, NO_TRAVEL)])
        self.assertTrue(summary.has_no_travel)


class RecommendTests(SimpleTestCase):
    def assert_pick(self, routes: list[RouteOption], route_id: str, why: str) -> None:
        result = recommend(routes)
        self.assertEqual((result.route_id, result.reason), (route_id, why))

    def test_empty_list_raises(self) -> None:
        with self.assertRaises(ValueError):
            recommend([])

    def test_single_route(self) -> None:
        self.assert_pick([route("A", severe=50)], "A", "Only route available")

    def test_no_travel_route_never_wins_over_safe_route(self) -> None:
        routes = [
            route("A", no_travel=5, duration_s=1_000),
            route("B", severe=200, high=300, avg_risk=2.5),
        ]
        self.assert_pick(routes, "B", "Avoids No Travel")

    def test_all_routes_no_travel_picks_fewest(self) -> None:
        routes = [route("A", no_travel=50), route("B", no_travel=10)]
        self.assert_pick(routes, "B", "Fewest No Travel miles")

    def test_fewest_severe_miles_first(self) -> None:
        routes = [route("A", severe=25, duration_s=1_000), route("B", high=100)]
        self.assert_pick(routes, "B", "Fewest Severe miles")

    def test_then_fewest_high_miles(self) -> None:
        routes = [route("A", high=50, avg_risk=0.1), route("B", high=25)]
        self.assert_pick(routes, "B", "Fewest High miles")

    def test_then_lowest_average_risk(self) -> None:
        routes = [route("A", avg_risk=0.8, duration_s=1_000), route("B", avg_risk=0.3)]
        self.assert_pick(routes, "B", "Lowest average risk")

    def test_then_shortest_travel_time(self) -> None:
        routes = [route("A", duration_s=40_000), route("B", duration_s=30_000)]
        self.assert_pick(routes, "B", "Shortest travel time")

    def test_unknown_average_ranks_last(self) -> None:
        routes = [route("A", avg_risk=None), route("B", avg_risk=3.0)]
        self.assert_pick(routes, "B", "Lowest average risk")

    def test_zero_average_beats_positive(self) -> None:
        routes = [route("A", avg_risk=0.2), route("B", avg_risk=0.0)]
        self.assert_pick(routes, "B", "Lowest average risk")

    def test_full_tie_keeps_first_route(self) -> None:
        self.assert_pick([route("A"), route("B")], "A", "Equal on all criteria")

    def test_three_routes(self) -> None:
        routes = [route("A", no_travel=10), route("B", severe=25), route("C", high=50)]
        self.assert_pick(routes, "C", "Fewest Severe miles")
