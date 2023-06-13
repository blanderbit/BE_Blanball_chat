from typing import Any, Optional

from chat.exceptions import NotFoundException
from chat.models import Chat


def get_chat(*, chat_id: Optional[int] = None, event_id: Optional[int] = None) -> Chat:
    try:
        if chat_id:
            chat_instance = Chat.objects.get(id=chat_id)
        else:
            chat_instance = Chat.objects.filter(event_id=event_id)[0]
    except Chat.DoesNotExist:
        raise NotFoundException(object="chat")
    except IndexError:
        raise NotFoundException(object="chat")
    return chat_instance
