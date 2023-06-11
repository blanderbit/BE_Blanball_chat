from chat.models import Messsage

MESSAGE_NOT_FOUND_ERROR: str = "message_not_found"


def get_message(*, message_id: int) -> Messsage:
    try:
        message_instance = Messsage.objects.get(id=message_id)

    except Messsage.DoesNotExist:
        raise ValueError(MESSAGE_NOT_FOUND_ERROR)
    return message_instance
