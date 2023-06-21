from typing import Any, Optional

from django.conf import settings
from django.db.models.query import QuerySet
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    InvalidDataException,
)
from chat.models import Messsage
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_is_chat_member,
    generate_response,
    get_message_without_error,
    add_request_data_to_response
)
from chat.decorators.set_required_fields import (
    set_required_fields
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "read_or_unread_messages"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "read_or_unread_messages_response"

ACTION_INVALID_ERROR: str = "action_invalid"


MESSAGE_TYPE: str = "read_or_unread_messages"

ACTION_OPTIONS: dict[str, str] = {"read": "read", "unread": "unread"}


message_data = dict[str, Any]

messages_objects: QuerySet[Messsage] = []


@set_required_fields(["request_user_id", "message_ids", "action"])
def validate_input_data(data: message_data) -> None:
    request_user_id: int = data.get("request_user_id")
    message_ids: int = data.get("message_ids")
    action: str = data.get("action")

    if action not in ACTION_OPTIONS:
        raise InvalidDataException(ACTION_INVALID_ERROR)

    global message_instance

    for message_id in message_ids:
        message_instance = get_message_without_error(message_id=message_id)

        if message_instance:
            chat_instance = message_instance.chat.first()

            if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
                return None
            if request_user_id == message_instance.sender_id:
                return None
            messages_objects.append(message_instance)


def read_or_unread_messages(*, user_id: int, action: str) -> list[Optional[int]]:
    success: list[Optional[int]] = []
    for message_obj in messages_objects:
        if action == ACTION_OPTIONS["read"]:
            message_obj.mark_as_read(user_id)
        else:
            message_obj.mark_as_unread(user_id)
        success.append(message_obj.id)
    return success


def read_or_unread_messages_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            validate_input_data(data.value)
            response_data = read_or_unread_messages(
                user_id=data.value["request_user_id"],
                action=data.value["action"],
            )
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_data=add_request_data_to_response(data.value)
                ),
            )
        except COMPARED_CHAT_EXCEPTIONS as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_data=add_request_data_to_response(data.value)
                ),
            )
