from datetime import UTC, datetime, timedelta

from django.test import SimpleTestCase

from planner.sampling import elapsed_seconds, haversine_miles, sample_checkpoints

DEPARTURE = datetime(2026, 10, 24, 13, 0, tzinfo=UTC)
MILES_PER_LAT_DEGREE = haversine_miles((0, 0), (1, 0))


def north(miles: float) -> tuple[float, float]:
    return (miles / MILES_PER_LAT_DEGREE, 0.0)


class HaversineTests(SimpleTestCase):
    def test_one_degree_of_latitude(self) -> None:
        self.assertAlmostEqual(MILES_PER_LAT_DEGREE, 69.09, places=1)

    def test_same_point_is_zero(self) -> None:
        self.assertEqual(haversine_miles((41.88, -87.63), (41.88, -87.63)), 0)

    def test_chicago_to_denver(self) -> None:
        miles = haversine_miles((41.88, -87.63), (39.74, -104.99))
        self.assertAlmostEqual(miles, 920, delta=10)


class ElapsedSecondsTests(SimpleTestCase):
    def test_one_span_is_split_by_distance(self) -> None:
        points = [north(0), north(10), north(30)]
        self.assertEqual(elapsed_seconds(points, [0], [300]), [0, 100, 300])

    def test_spans_with_different_speeds(self) -> None:
        points = [north(0), north(10), north(20), north(30)]
        result = elapsed_seconds(points, [0, 2], [600, 1200])
        for actual, expected in zip(result, [0, 300, 600, 1800]):
            self.assertAlmostEqual(actual, expected)

    def test_zero_length_span_adds_time_at_its_end(self) -> None:
        points = [north(0), north(0), north(10)]
        result = elapsed_seconds(points, [0, 1], [60, 600])
        self.assertEqual(result, [0, 60, 660])


class SampleCheckpointsTests(SimpleTestCase):
    def setUp(self) -> None:
        self.points = [north(0), north(100)]
        self.elapsed = [0.0, 7200.0]

    def sample(self, interval_mi: float) -> list:
        return sample_checkpoints(self.points, self.elapsed, DEPARTURE, interval_mi)

    def test_every_25_miles_ends_at_destination(self) -> None:
        checkpoints = self.sample(25)
        self.assertEqual([round(c.mile, 3) for c in checkpoints], [25, 50, 75, 100])
        self.assertEqual([round(c.segment_miles, 3) for c in checkpoints], [25] * 4)

    def test_last_checkpoint_covers_remainder(self) -> None:
        checkpoints = self.sample(30)
        self.assertEqual([round(c.mile, 3) for c in checkpoints], [30, 60, 90, 100])
        self.assertAlmostEqual(checkpoints[-1].segment_miles, 10)

    def test_segments_add_up_to_route_length(self) -> None:
        for interval in (10, 25, 50):
            with self.subTest(interval=interval):
                total = sum(c.segment_miles for c in self.sample(interval))
                self.assertAlmostEqual(total, 100)

    def test_route_shorter_than_interval(self) -> None:
        self.points = [north(0), north(10)]
        self.elapsed = [0.0, 720.0]
        checkpoints = self.sample(25)
        self.assertEqual(len(checkpoints), 1)
        self.assertAlmostEqual(checkpoints[0].mile, 10)
        self.assertAlmostEqual(checkpoints[0].segment_miles, 10)

    def test_eta_uses_elapsed_time(self) -> None:
        checkpoints = self.sample(25)
        self.assertEqual(checkpoints[0].eta, DEPARTURE + timedelta(minutes=30))
        self.assertEqual(checkpoints[-1].eta, DEPARTURE + timedelta(hours=2))

    def test_position_is_interpolated(self) -> None:
        checkpoint = self.sample(50)[0]
        self.assertAlmostEqual(checkpoint.lat, north(50)[0])
        self.assertAlmostEqual(checkpoint.lon, 0)

    def test_eta_follows_uneven_speed(self) -> None:
        self.points = [north(0), north(50), north(100)]
        self.elapsed = [0.0, 3600.0, 5400.0]
        checkpoints = self.sample(25)
        expected_minutes = [30, 60, 75, 90]
        for checkpoint, minutes in zip(checkpoints, expected_minutes):
            with self.subTest(mile=checkpoint.mile):
                self.assertEqual(checkpoint.eta, DEPARTURE + timedelta(minutes=minutes))
