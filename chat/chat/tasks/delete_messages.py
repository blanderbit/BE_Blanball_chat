from typing import Any, Optional

from django.conf import settings
from django.db.models.query import QuerySet
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    NotProvidedException,
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
    prepare_response,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "delete_messages"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "delete_messages_response"

MESSAGE_TYPE: str = "delete_messages"


message_data = dict[str, Any]

messages_objects: QuerySet[Messsage] = []


def validate_input_data(data: message_data) -> None:
    user_id: Optional[int] = data.get("user_id")
    message_ids: Optional[int] = data.get("message_ids")

    if not user_id:
        raise NotProvidedException(fields=["user_id"])
    if not message_ids or len(message_ids) == 0:
        raise NotProvidedException(fields=["message_ids"])

    global message_instance

    for message_id in message_ids:
        message_instance = get_message_without_error(message_id=message_id)

        if message_instance:
            chat_instance = message_instance.chat.first()

            if not check_user_is_chat_member(chat=chat_instance, user_id=user_id):
                return None
            if chat_instance.disabled:
                return None
            if user_id != message_instance.sender_id:
                return None
            messages_objects.append(message_instance)


def delete_messages(*, messages: QuerySet[Messsage]) -> Optional[str]:
    success: list[int] = []
    for message_obj in messages:
        message_id = message_obj.id
        message_obj.delete()
        success.append(message_id)
    return success


def delete_messages_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = delete_messages(
                messages=messages_objects,
            )
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id,
                ),
            )
        except COMPARED_CHAT_EXCEPTIONS as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=prepare_response(data=str(err)),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id,
                ),
            )
