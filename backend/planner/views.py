from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from planner.errors import PlannerError
from planner.plan import plan_trip
from planner.serializers import parse_plan_request


@api_view(["GET"])
def health(request: Request) -> Response:
    return Response({"status": "ok"})


@api_view(["POST"])
def plan(request: Request) -> Response:
    try:
        plan_request = parse_plan_request(request.data)
    except ValidationError as error:
        return Response(
            {
                "error": "invalid_input",
                "message": "Please check the highlighted fields.",
                "fields": error.detail,
            },
            status=400,
        )

    try:
        return Response(plan_trip(plan_request))
    except PlannerError as error:
        return Response(
            {"error": error.code, "message": error.message}, status=error.status
        )
