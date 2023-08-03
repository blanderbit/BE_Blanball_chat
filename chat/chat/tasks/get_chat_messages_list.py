from typing import Any, Optional

from chat.decorators import set_required_fields
from chat.exceptions import NotFoundException
from chat.models import Chat
from chat.serializers import (
    MessagesListSerializer,
)
from chat.utils import (
    check_user_in_chat,
    custom_pagination,
    find_user_in_chat_by_id,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chat_messages_list"

chat_data = dict[str, Any]


@set_required_fields(["request_user_id", "chat_id"])
def validate_input_data(data: chat_data) -> None:
    request_user_id: int = data.get("request_user_id")
    chat_id: int = data.get("chat_id")

    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_in_chat(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    return {
        "chat": chat_instance,
    }


def get_chat_messages_list(*, data: chat_data, chat: Chat) -> dict[str, Any]:
    offset: int = data.get("offset", 10)
    page: int = data.get("page", 1)
    search: Optional[str] = data.get("search")
    request_user_id: int = data.get("request_user_id")

    request_user = find_user_in_chat_by_id(users=chat.users, user_id=request_user_id)
    request_user_last_visble_message_id = request_user.get("last_visble_message_id")

    queryset = chat.messages.all()

    if request_user_last_visble_message_id:
        queryset = queryset.filter(id__lt=request_user_last_visble_message_id)

    if search:
        queryset = queryset.filter(text__icontains=search)

    return custom_pagination(
        queryset=queryset,
        offset=offset,
        page=page,
        serializer_class=MessagesListSerializer,
    )
