from typing import Any, Optional, Union

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


def get_request_for_chat_without_error(
        *,
        user_id_for_request_chat: int,
        request_user_id: int) -> Optional[Chat]:

    try:
        return Chat.get_only_available_chats_for_user_without_sortering(
            request_user_id
        ).filter(chat_request_user_id=user_id_for_request_chat)[0]
    except IndexError:
        pass
