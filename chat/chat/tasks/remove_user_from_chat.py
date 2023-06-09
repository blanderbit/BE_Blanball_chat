from typing import Any

from kafka import KafkaConsumer, KafkaProducer
from django.conf import settings
from chat.models import Chat
from chat.tasks.utils import (
    RESPONSE_STATUSES,
    generate_response,
)
from chat.tasks.default_producer import (
    default_producer
)


TOPIC_NAME: str = 'remove_user_from_chat'
RESPONSE_TOPIC_NAME: str = 'remove_user_from_chat_response'

MESSAGE_TYPE: str = 'remove_user_from_chat'

USER_ID_NOT_PROVIDED_ERROR: str = 'user_id_not_provided'
CHAT_ID_NOT_PROVIDED_ERROR: str = 'chat_id_not_provided'
CHAT_NOT_FOUND_ERROR: str = 'chat_not_found'
CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT: str = 'cant_remove_user_who_not_in_the_chat'

chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    event_id = data.get("event_id")

    if not user_id:
        raise ValueError(USER_ID_NOT_PROVIDED_ERROR)
    if not chat_id:
        raise ValueError(CHAT_ID_NOT_PROVIDED_ERROR)

    try:
        global chat_instance

        if chat_id:
            chat_instance = Chat.objects.get(id=chat_id)
        else:
            chat_instance = Chat.objects.filter(event_id=event_id)[0]

            if not chat_instance:
                raise ValueError(CHAT_NOT_FOUND_ERROR)

        if not any(user['user_id'] == user_id for user in chat_instance.users):
            raise ValueError(CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT)

    except Chat.DoesNotExist:
        raise ValueError(CHAT_NOT_FOUND_ERROR)


def remove_user_from_chat() -> None:
    pass


def remove_user_from_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG)

    for data in consumer:

        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = remove_user_from_chat(data.value.get("user_id"))
            default_producer(
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                )
            )
        except ValueError as err:
            default_producer(
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                )
            )
