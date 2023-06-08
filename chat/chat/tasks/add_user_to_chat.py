from typing import Any

from kafka import KafkaConsumer, KafkaProducer
from django.conf import settings
from chat.models import Chat
from chat.tasks.utils import (
    RESPONSE_STATUSES,
    generate_response,
)

TOPIC_NAME: str = 'add_user_to_chat'
RESPONSE_TOPIC_NAME: str = 'add_user_to_chat_response'

MESSAGE_TYPE: str = 'add_user_to_chat'

USER_ID_NOT_PROVIDED_ERROR: str = 'user_id_not_provided'
CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR: str = 'chat_id_or_event_id_not_provided'
CANT_ADD_USER_TO_PERSONAL_CHAT_ERROR: str = 'cant_add_user_to_personal_chat'
CHAT_NOT_FOUND_ERROR: str = 'chat_not_found'
CANT_ADD_USER_WHO_IS_ALREADY_IN_THE_CHAT_ERROR: str = 'cant_add_user_who_is_already_in_the_chat'

USER_ADDED_TO_CHAT_SUCCESS: dict[str, str] = {"success": "user_added_to_chat"}

chat_data = dict[str, Any]


def add_user_to_chat_response_producer(response_data: Any) -> None:
    producer: KafkaProducer = KafkaProducer(**settings.KAFKA_PRODUCER_CONFIG)
    producer.send(RESPONSE_TOPIC_NAME, value=response_data)
    producer.flush()


def validate_input_data(data: chat_data) -> None:
    user_id = data.get('user_id')
    event_id = data.get('event_id')
    chat_id = data.get('chat_id')

    print(user_id)

    if not user_id:
        raise ValueError(USER_ID_NOT_PROVIDED_ERROR)
    if not event_id and not chat_id:
        raise ValueError(CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR)

    try:
        global chat_instance

        if chat_id:
            chat_instance = Chat.objects.get(id=chat_id)
        else:
            chat_instance = Chat.objects.filter(event_id=event_id)[0]

            if not chat_instance:
                raise ValueError(CHAT_NOT_FOUND_ERROR)

        if chat_instance.type == Chat.Type.PERSONAL:
            raise ValueError(CANT_ADD_USER_TO_PERSONAL_CHAT_ERROR)
        elif any(user['user_id'] == user_id for user in chat_instance.users):
            raise ValueError(CANT_ADD_USER_WHO_IS_ALREADY_IN_THE_CHAT_ERROR)

    except Chat.DoesNotExist:
        raise ValueError(CHAT_NOT_FOUND_ERROR)


def add_user_to_chat(user_id: int) -> None:
    chat_instance.users.append({
        "author": False,
        "disabled": False,
        "user_id": user_id,
    })

    return USER_ADDED_TO_CHAT_SUCCESS


def add_user_to_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG)

    for data in consumer:

        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = add_user_to_chat(data.value.get("user_id"))
            add_user_to_chat_response_producer(
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                )
            )
        except ValueError as err:
            add_user_to_chat_response_producer(
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                )
            )
