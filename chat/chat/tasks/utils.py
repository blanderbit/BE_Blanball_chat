
from typing import Any, Optional


RESPONSE_STATUSES: dict[str, str] = {
    "ERROR": "error",
    "SUCCESS": "success"
}


def generate_response(*, 
        status: str, 
        data: Any,
        message_type: str, 
        request_id: Optional[str] = None
    ) -> dict[str, Any]:
    if (request_id):
        return {
            "message_type": message_type,
            "request_id": request_id,
            "status": status,
            "data": data,
        }
    return {
        "message_type": message_type,
        "status": status,
        "data": data
    }


def create_user_data_before_add_to_chat(*,
        is_author: bool, 
        is_disabled: bool = False,
        is_removed: bool = False, 
        user_id: int,
    ) -> dict[str, Any]:

    return {
        "author": is_author,
        "disabled": is_disabled,
        "user_id": user_id,
        "removed": is_removed,
    }