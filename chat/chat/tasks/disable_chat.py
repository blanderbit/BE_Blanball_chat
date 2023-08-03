from typing import Any, Optional, Union

from chat.decorators import set_required_fields
from chat.models import Chat
from chat.utils import get_chat

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "disable_chat"

chat_data = dict[str, Any]


@set_required_fields([["chat_id", "event_id"]])
def validate_input_data(data: chat_data) -> None:
    chat_id: Optional[int] = data.get("chat_id")
    event_id: Optional[int] = data.get("event_id")

    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    return {"chat": chat_instance}


def disable_chat(*, chat: Chat) -> None:
    chat.disabled = True
    chat.save()

    response_data: dict[str, Union[int, list[int]]] = {
        "users": chat.users,
        "chat_id": chat.id,
    }

    return response_data
