from typing import Any, Optional

from django.db.models.query import QuerySet

from chat.decorators import set_required_fields
from chat.exceptions import NotFoundException
from chat.models import Chat, Messsage
from chat.utils import (
    check_user_is_chat_member,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "delete_messages"

message_data = dict[str, Any]


@set_required_fields(["message_ids", "request_user_id", "chat_id"])
def validate_input_data(data: message_data) -> None:
    request_user_id: int = data.get("request_user_id")
    chat_id: int = data.get("chat_id")
    message_ids: list[Optional[int]] = data.get("message_ids")

    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    messages: QuerySet[Messsage] = chat_instance.messages.filter(id__in=message_ids)
    messages_objects: list[Optional[Messsage]] = []

    for message in messages:
        if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
            return None
        if chat_instance.disabled:
            return None
        if request_user_id != message.sender_id:
            return None
        if message.service:
            return None
        messages_objects.append(message)
    return {"messages": messages_objects, "chat": chat_instance}


def delete_messages(*, messages: QuerySet[Messsage], chat: Chat) -> list[Optional[int]]:
    success: list[Optional[int]] = []
    for message_obj in messages:
        message_id = message_obj.id
        message_obj.delete()
        success.append(message_id)
    return {
        "users": chat.users_in_the_chat,
        "chat_id": chat.id,
        "messages_ids": success,
    }
