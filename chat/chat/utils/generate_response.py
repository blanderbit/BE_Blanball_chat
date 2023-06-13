from typing import Any, Optional
from django.utils import timezone

RESPONSE_STATUSES: dict[str, str] = {"ERROR": "error", "SUCCESS": "success"}


def generate_response(
    *, status: str, data: Any, message_type: str, request_id: Optional[str] = None
) -> dict[str, Any]:

    current_time = str(timezone.now())
    if request_id:
        return {
            "message_type": message_type,
            "date_and_time": current_time,
            "request_id": request_id,
            "status": status,
            "data": data,
        }
    return {
        "message_type": message_type,
        "date_and_time": current_time,
        "status": status,
        "data": data,
    }
