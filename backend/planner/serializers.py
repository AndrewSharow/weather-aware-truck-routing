from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from django.utils import timezone
from rest_framework import serializers

MAX_LOAD_LB = 45_000
INTERVALS_MI = [10, 25, 50]
MAX_DAYS_AHEAD = 7
PAST_TOLERANCE = timedelta(minutes=5)


@dataclass(frozen=True)
class PlanRequest:
    origin: str
    destination: str
    departure: datetime
    load_lb: int
    interval_mi: int


class PlanRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=200)
    destination = serializers.CharField(max_length=200)
    departure = serializers.DateTimeField()
    load_lb = serializers.IntegerField(min_value=0, max_value=MAX_LOAD_LB)
    interval_mi = serializers.ChoiceField(choices=INTERVALS_MI)

    def validate_departure(self, value: datetime) -> datetime:
        now = timezone.now()
        if value < now - PAST_TOLERANCE:
            raise serializers.ValidationError("Departure can't be in the past.")
        if value > now + timedelta(days=MAX_DAYS_AHEAD):
            raise serializers.ValidationError(
                f"Departure must be within the next {MAX_DAYS_AHEAD} days."
            )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["origin"].casefold() == attrs["destination"].casefold():
            raise serializers.ValidationError(
                {"destination": "Destination must be different from origin."}
            )
        return attrs


def parse_plan_request(data: Any) -> PlanRequest:
    serializer = PlanRequestSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return PlanRequest(**cast(dict[str, Any], serializer.validated_data))
