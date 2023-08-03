from typing import Any, Optional

from chat.decorators.set_required_fields import (
    set_required_fields,
)
from chat.exceptions import InvalidActionException
from chat.models import Messsage
from chat.utils import (
    check_user_is_chat_member,
    get_message_without_error,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "read_or_unread_messages"

ACTION_OPTIONS: dict[str, str] = {"read": "read", "unread": "unread"}


message_data = dict[str, Any]


@set_required_fields(["request_user_id", "message_ids", "action"])
def validate_input_data(data: message_data) -> None:
    request_user_id: int = data.get("request_user_id")
    message_ids: int = data.get("message_ids")
    action: str = data.get("action")

    if action not in ACTION_OPTIONS:
        raise InvalidActionException

    messages_objects: list[Optional[Messsage]] = []

    for message_id in message_ids:
        message_instance = get_message_without_error(message_id=message_id)

        if message_instance:
            chat_instance = message_instance.chat.first()

            if not check_user_is_chat_member(
                chat=chat_instance, user_id=request_user_id
            ):
                return None
            if request_user_id == message_instance.sender_id:
                return None
            messages_objects.append(message_instance)
    return {"messages": message_instance}


def read_or_unread_messages(
    *, user_id: int, action: str, messages: list[Optional[Messsage]]
) -> list[Optional[int]]:
    success: list[Optional[int]] = []
    for message_obj in messages:
        if action == ACTION_OPTIONS["read"]:
            message_obj.mark_as_read(user_id)
        else:
            message_obj.mark_as_unread(user_id)
        success.append(message_obj.id)
    return success
