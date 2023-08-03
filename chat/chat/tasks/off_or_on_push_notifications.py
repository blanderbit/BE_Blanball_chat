from typing import Any

from chat.decorators.set_required_fields import (
    set_required_fields,
)
from chat.exceptions import (
    InvalidActionException,
    NotFoundException,
)
from chat.models import Chat
from chat.utils import (
    check_user_is_chat_member,
    find_user_in_chat_by_id,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "off_or_on_push_notifications"

ACTION_OPTIONS: dict[str, str] = {"on": "on", "off": "off"}


@set_required_fields(["request_user_id", "chat_id", "action"])
def validate_input_data(data: dict[str, Any]) -> None:
    request_user_id: int = data.get("request_user_id")
    action: str = data.get("action")
    chat_id: int = data.get("chat_id")

    chat_instance = get_chat(chat_id=chat_id)

    if action not in ACTION_OPTIONS:
        raise InvalidActionException

    if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    return {"chat": chat_instance}


def off_or_on_push_notifications(*, data: dict[str, Any], chat: Chat) -> None:
    user_id: int = data["request_user_id"]
    action: str = data["action"]

    user_to_remove = find_user_in_chat_by_id(users=chat.users, user_id=user_id)

    user_to_remove["push_notifications"] = action == ACTION_OPTIONS["on"]

    chat.save()

    response_data: dict[str, Any] = {
        "chat_id": chat.id,
        "action": action,
    }

    return response_data
