from typing import Any, Optional

RESPONSE_STATUSES: dict[str, str] = {"ERROR": "error", "SUCCESS": "success"}


def generate_response(
    *, status: str, data: Any, message_type: str, request_id: Optional[str] = None
) -> dict[str, Any]:
    if request_id:
        return {
            "message_type": message_type,
            "request_id": request_id,
            "status": status,
            "data": data,
        }
    return {"message_type": message_type, "status": status, "data": data}
