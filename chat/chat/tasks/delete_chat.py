from typing import Any, Optional, Union

from chat.decorators.set_required_fields import (
    set_required_fields,
)
from chat.exceptions import (
    NotFoundException,
    PermissionsDeniedException,
)
from chat.models import Chat
from chat.tasks.remove_user_from_chat import (
    remove_user_from_chat,
)
from chat.utils import (
    check_is_all_users_deleted_personal_chat,
    check_user_is_chat_admin,
    check_user_is_chat_member,
    find_user_in_chat_by_id,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "delete_chat"

YOU_DONT_HAVE_PERMISSIONS_TO_DELETE_THIS_CHAT_ERROR: str = (
    "you_dont_have_permissions_to_delete_this_chat"
)

chat_data = dict[str, Any]


@set_required_fields(["request_user_id", ["event_id", "chat_id"]])
def validate_input_data(data: chat_data) -> None:
    request_user_id: int = data.get("request_user_id")
    chat_id: Optional[int] = data.get("chat_id")
    event_id: Optional[int] = data.get("event_id")

    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if chat_instance.is_group:
        if not check_user_is_chat_admin(chat=chat_instance, user_id=request_user_id):
            raise PermissionsDeniedException(
                YOU_DONT_HAVE_PERMISSIONS_TO_DELETE_THIS_CHAT_ERROR
            )
    else:
        if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
            raise NotFoundException(object="chat")

    return {"chat": chat_instance}


def set_chat_deleted_by_certain_user(*, user: dict[str, Any], chat: Chat) -> None:
    user["chat_deleted"] = True
    chat.save()


def delete_chat(*, data: dict[str, Any], chat: Chat) -> None:
    user = find_user_in_chat_by_id(users=chat.users, user_id=data["request_user_id"])
    if chat.type == Chat.Type.PERSONAL:
        set_chat_deleted_by_certain_user(user=user, chat=chat)

        if check_is_all_users_deleted_personal_chat(chat=chat):
            chat.delete()
    else:
        if user["author"]:
            chat.delete()
        else:
            remove_user_from_chat(user_id=user["request_user_id"], chat=chat)

    response_data: dict[str, Union[int, list[int]]] = {
        "users": chat.users,
        "chat_id": chat.id,
    }

    return response_data
