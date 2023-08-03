from typing import Any, Optional

from chat.decorators import set_required_fields
from chat.exceptions import (
    PermissionsDeniedException,
)
from chat.models import Chat
from chat.utils import (
    check_user_is_chat_author,
    check_user_is_chat_member,
    find_user_in_chat_by_id,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "remove_user_from_chat"

CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT: str = "cant_remove_user_who_not_in_the_chat"
YOU_DONT_HAVE_PERMISSIONS_TO_REMOVE_USER_FROM_THIS_CHAT_ERROR: str = (
    "you_dont_have_permissions_to_remove_user_from_this_chat"
)
CANT_REMOVE_USER_FROM_PERSONAL_CHAT: str = "cant_remove_user_from_personal_chat"


chat_data = dict[str, Any]


@set_required_fields(["user_id", ["chat_id", "event_id"]])
def validate_input_data(data: chat_data) -> None:
    user_id: int = data.get("user_id")
    chat_id: Optional[int] = data.get("chat_id")
    event_id: Optional[int] = data.get("event_id")
    request_user_id: Optional[int] = data.get("request_user_id")

    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if request_user_id:
        if chat_instance.type == Chat.Type.PERSONAL:
            raise PermissionsDeniedException(CANT_REMOVE_USER_FROM_PERSONAL_CHAT)

        if not check_user_is_chat_author(chat=chat_instance, user_id=request_user_id):
            raise PermissionsDeniedException(
                YOU_DONT_HAVE_PERMISSIONS_TO_REMOVE_USER_FROM_THIS_CHAT_ERROR
            )

    if not check_user_is_chat_member(chat=chat_instance, user_id=user_id):
        raise PermissionsDeniedException(CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT)

    return {"chat": chat_instance}


def remove_user_from_chat(*, data: dict[str, Any], chat: Chat) -> str:
    user_id: int = data["user_id"]
    request_user_id: Optional[int] = request_user_id.get("request_user_id")

    user_to_remove = find_user_in_chat_by_id(users=chat.users, user_id=user_id)

    if user_to_remove:
        if (
            chat.type == Chat.Type.GROUP or chat.type == Chat.Type.EVENT_GROUP
        ) and request_user_id:
            user_to_remove["removed"] = True
            chat_last_message = chat.messages.last()
            chat_last_message_id = chat_last_message.id if chat_last_message else 0
            user_to_remove["last_visble_message_id"] = chat_last_message_id
        else:
            chat.users.remove(user_to_remove)
        chat.save()
    if len(chat.users_in_the_chat) == 0:
        chat.delete()

    print(chat.users_in_the_chat.append(user_to_remove))

    response_data: dict[str, Any] = {
        "users": chat.users_in_the_chat.append(user_to_remove),
        "chat_id": chat.id,
        "removed_user_id": user_id,
    }

    return response_data
