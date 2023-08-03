from typing import Any, Optional

from django.db.models.query import QuerySet

from chat.decorators import set_required_fields
from chat.models import Chat
from chat.serializers import ChatsListSerializer
from chat.utils import custom_pagination

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chats_list"

AVILABLE_CHATS_TYPE_FILTER: dict[str, str] = {
    "dialog": "dialog",
    "group": "group",
    "request": "request",
}


chat_data = dict[str, Any]


@set_required_fields(["request_user_id"])
def validate_input_data(data: chat_data) -> None:
    pass


def get_chats_list(*, data: chat_data) -> dict[str, Any]:
    request_user_id: Optional[int] = data.get("request_user_id")
    offset: int = data.get("offset", 10)
    page: int = data.get("page", 1)
    search: Optional[str] = data.get("search")
    chats_type: Optional[str] = data.get("chats_type")

    queryset: QuerySet[Chat] = Chat.get_only_available_chats_for_user(
        user_id=request_user_id
    )

    if search:
        queryset = queryset.filter(name__icontains=search)
    if chats_type:
        if chats_type == "dialog":
            queryset = queryset.filter(type=Chat.Type.PERSONAL)
        elif chats_type == "group":
            queryset = queryset.filter(type__in=Chat.CHAT_GROUP_TYPES())
        elif chats_type == "request":
            queryset = queryset.filter(
                users__contains=[
                    {
                        "user_id": request_user_id,
                        "chat_request": True,
                    }
                ]
            )

    return custom_pagination(
        queryset=queryset,
        offset=offset,
        page=page,
        serializer_class=ChatsListSerializer,
        serializer_context={"request_user_id": request_user_id},
    )
