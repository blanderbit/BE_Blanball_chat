from typing import Any, Union


def add_request_data_to_response(
    data: dict[str, Any]
) -> dict[str, dict[str, Union[str, int, None]]]:
    return {
        "request_id": data.get("request_id"),
        "request_user_id": data.get("request_user_id"),
    }
