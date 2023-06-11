from typing import Any, Optional

from chat.models import Chat

CHAT_NOT_FOUND_ERROR: str = "chat_not_found"


def get_chat(*, chat_id: Optional[int] = None, event_id: Optional[int] = None) -> Chat:
    try:
        if chat_id:
            chat_instance = Chat.objects.get(id=chat_id)
        else:
            chat_instance = Chat.objects.filter(event_id=event_id)[0]
    except Chat.DoesNotExist:
        raise ValueError(CHAT_NOT_FOUND_ERROR)
    except IndexError:
        raise ValueError(CHAT_NOT_FOUND_ERROR)
    return chat_instance
