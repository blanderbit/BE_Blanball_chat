from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.models import (
    Messsage,
    Chat
)
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    generate_response,
    get_message,
    remove_unnecessary_data,
    check_user_is_chat_member,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "edit_message"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "edit_message_response"

USER_ID_NOT_PROVIDED_ERROR: str = "user_id_not_provided"
MESSAGE_ID_NOT_PROVIDED_ERROR: str = "message_id_not_provided"
MESSAGE_NOT_PROVIDED_ERROR: str = "message_not_provided"
CANT_EDIT_MESSAGE_IN_DISABLED_CHAT_ERROR: str = "cant_edit_message_in_disabled_chat"
PROVIDED_DATA_INVALID_TO_EDIT_THE_MESSAGE_ERROR: str = "provided_data_invalid_to_edit_the_message"
TIME_TO_EDIT_THE_MESSAGE_EXPIRED_ERROR: str = "time_to_edit_the_message_expired"
YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_MESSAGE_ERROR: str = "you_dont_have_permissions_to_edit_this_message"
CHAT_NOT_FOUND_ERROR: str = "chat_not_found"
MESSAGE_EDITED_SUCCESS: str = "message_edited"


EDIT_MESSAGE_FIELDS: list[str] = ["text", "id"]

MESSAGE_TYPE: str = "edit_message"


message_data = dict[str, Any]
chat_instance: Optional[Chat] = None


def validate_input_data(data: message_data) -> None:
    user_id: Optional[int] = data.get("user_id")
    message_id: Optional[int] = data.get("message_id")

    if not user_id:
        raise ValueError(USER_ID_NOT_PROVIDED_ERROR)
    if not message_id:
        raise ValueError(MESSAGE_ID_NOT_PROVIDED_ERROR)

    global message_instance
    message_instance = get_message(message_id=message_id)
    chat_instance = message_instance.chat.first()

    if not check_user_is_chat_member(chat=chat_instance, user_id=user_id):
        raise ValueError(CHAT_NOT_FOUND_ERROR)

    if message_instance.sender_id != user_id:
        raise ValueError(YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_MESSAGE_ERROR)

    if chat_instance.disabled:
        raise ValueError(CANT_EDIT_MESSAGE_IN_DISABLED_CHAT_ERROR)

    if message_instance.is_expired_to_edit():
        raise ValueError(TIME_TO_EDIT_THE_MESSAGE_EXPIRED_ERROR)


def prepare_data_before_edit_message(*, data: message_data) -> message_data:
    prepared_data = remove_unnecessary_data(
        data, *EDIT_MESSAGE_FIELDS
    )

    return prepared_data


def edit_message(*, message: Messsage, new_data: message_data) -> Optional[str]:
    try:
        prepared_data = prepare_data_before_edit_message(data=new_data)

        message.__dict__.update(prepared_data)
        message.edited = True
        message.save()

        return {
            "chat_id": chat_instance.id,
            "users": chat_instance.users,
            "new_data": remove_unnecessary_data(message.__dict__)
        }
    except Exception:
        raise ValueError(PROVIDED_DATA_INVALID_TO_EDIT_THE_MESSAGE_ERROR)


def edit_message_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = edit_message(
                message=message_instance,
                new_data=data.value["new_data"],
            )
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                ),
            )
        except ValueError as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                ),
            )
