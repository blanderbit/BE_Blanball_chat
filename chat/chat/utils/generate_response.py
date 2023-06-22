from typing import Any, Optional

from django.utils import timezone

RESPONSE_STATUSES: dict[str, str] = {"ERROR": "error", "SUCCESS": "success"}


def generate_response(
    *, status: str, data: Any, message_type: str, request_data: Optional[str] = None
) -> dict[str, Any]:
    response_data: dict[str, Any] = {
        "message_type": message_type,
        "date_and_time": str(timezone.now()),
        "status": status,
        "data": data,
    }
    if request_data:
        response_data["request_data"] = request_data
    return response_data
