from typing import Any

from chat.decorators import set_required_fields
from chat.exceptions import NotFoundException
from chat.models import Chat
from chat.utils import (
    check_user_is_chat_member,
    custom_json_field_pagination,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chat_users_list"


@set_required_fields(["request_user_id", "chat_id"])
def validate_input_data(data: dict[str, int]) -> None:
    request_user_id: int = data.get("request_user_id")
    chat_id: int = data.get("chat_id")

    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    return {"chat": chat_instance}


def get_chat_users_list(*, data: dict[str, int], chat: Chat) -> dict[str, Any]:
    offset: int = data.get("offset", 10)
    page: int = data.get("page", 1)

    helpfull_data: dict[str, str] = {
        "chat_users_count_limit": chat.chat_users_count_limit,
    }
    filter_params: dict[str, bool] = {"removed": False, "chat_deleted": False}

    return custom_json_field_pagination(
        model_instance=chat,
        page=page,
        offset=offset,
        field_name="users",
        filter_params=filter_params,
        helpfull_data=helpfull_data,
    )
