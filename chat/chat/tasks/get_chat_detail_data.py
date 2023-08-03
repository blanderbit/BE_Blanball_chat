from typing import Any

from chat.decorators import set_required_fields
from chat.exceptions import NotFoundException
from chat.models import Chat
from chat.utils import (
    check_user_in_chat,
    find_user_in_chat_by_id,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chat_detail_data"


@set_required_fields(["request_user_id", "chat_id"])
def validate_input_data(data: dict[str, int]) -> None:
    request_user_id: int = data.get("request_user_id")
    chat_id: int = data.get("chat_id")

    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_in_chat(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    return {"chat": chat_instance}


def get_chat_detail_data(*, data: dict[str, int], chat: Chat) -> dict[str, Any]:
    request_user = find_user_in_chat_by_id(
        users=chat.users, user_id=data["request_user_id"]
    )

    chat_data: dict[str, bool] = {
        "chat_data": {
            "id": chat.id,
            "name": chat.name,
            "image": chat.image,
            "disabled": chat.disabled,
            "type": chat.type,
        },
        "request_user_data": {
            "author": request_user["author"],
            "disabled": request_user["disabled"],
            "removed": request_user["removed"],
            "admin": request_user["admin"],
            "chat_request": request_user["chat_request"],
            "push_notifications": request_user["push_notifications"],
        },
    }

    return chat_data
