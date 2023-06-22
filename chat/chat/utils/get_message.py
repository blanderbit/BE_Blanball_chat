from typing import Optional

from chat.exceptions import NotFoundException
from chat.models import Messsage


def get_message(*, message_id: int) -> Messsage:
    try:
        message_instance = Messsage.objects.get(id=message_id)

    except Messsage.DoesNotExist:
        raise NotFoundException(object="message")
    return message_instance


def get_message_without_error(*, message_id: int) -> Optional[Messsage]:
    try:
        message_instance = Messsage.objects.get(id=message_id)
        return message_instance
    except Messsage.DoesNotExist:
        pass
