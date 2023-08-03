from typing import Any, Optional

from chat.decorators import set_required_fields
from chat.exceptions import (
    InvalidDataException,
    NotProvidedException,
    PermissionsDeniedException,
)
from chat.models import Chat
from chat.utils import (
    check_user_is_chat_admin,
    get_chat,
    remove_unnecessary_data,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "edit_chat"

CANT_EDIT_DISABLED_CHAT_ERROR: str = "chat_edit_disabled_chat"
YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_CHAT_ERROR: str = (
    "you_dont_have_permissions_to_edit_this_chat"
)

KEYS_IN_NEW_DATA_TO_KEEP: list[str] = ["name", "image"]


chat_data = dict[str, Any]


@set_required_fields([["chat_id", "event_id"]])
def validate_input_data(data: chat_data) -> None:
    chat_id: Optional[int] = data.get("chat_id")
    event_id: Optional[int] = data.get("event_id")
    request_user_id: Optional[int] = data.get("request_user_id")

    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if chat_instance.disabled:
        raise PermissionsDeniedException(CANT_EDIT_DISABLED_CHAT_ERROR)
    if not request_user_id and chat_instance.is_group:
        raise NotProvidedException(fields=["request_user_id"])
    elif request_user_id and chat_instance.is_group:
        if not check_user_is_chat_admin(chat=chat_instance, user_id=request_user_id):
            raise PermissionsDeniedException(
                YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_CHAT_ERROR
            )

    return {"chat": chat_instance}


def edit_chat(*, data: dict[str, Any], chat: Chat) -> Optional[str]:
    new_chat_data: dict[str, Any] = data["new_data"]

    try:
        prepared_data = remove_unnecessary_data(
            new_chat_data, *KEYS_IN_NEW_DATA_TO_KEEP
        )
        chat.__dict__.update(**prepared_data)
        chat.save()

        response_data: dict[str, Any] = {
            "users": chat.users,
            "chat_id": chat.id,
            "new_data": remove_unnecessary_data(
                chat.__dict__, *KEYS_IN_NEW_DATA_TO_KEEP
            ),
        }

        return response_data

    except Exception as _err:
        print(_err)
        raise InvalidDataException
