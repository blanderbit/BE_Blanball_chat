from typing import Any

from kafka import KafkaConsumer, KafkaProducer
from django.conf import settings
from chat.models import Chat
from chat.tasks.utils import (
    RESPONSE_STATUSES,
    generate_response,
)

TOPIC_NAME: str = 'create_chat'
RESPONSE_TOPIC_NAME: str = 'create_chat_response'
CHAT_NAME_NOT_PROVIDED_ERROR: str = 'name_not_provided'
CHAT_AUTOR_NOT_PROVIDED_ERROR: str = 'author_not_provided'
REQUEST_ID_NOT_PROVIDED_ERROR: str = 'request_id_not_provided'

MESSAGE_TYPE: str = 'create_chat'


chat_data = dict[str, Any]


def create_chat_response_producer(response_data: Any) -> None:
    producer: KafkaProducer = KafkaProducer(**settings.KAFKA_PRODUCER_CONFIG)
    producer.send(RESPONSE_TOPIC_NAME, value=response_data)
    producer.flush()


def validate_input_data(data: chat_data) -> None:
    if not data.get('name'):
        raise ValueError(CHAT_NAME_NOT_PROVIDED_ERROR)
    if not data.get('author'):
        raise ValueError(CHAT_AUTOR_NOT_PROVIDED_ERROR)
    if not data.get('request_id'):
        raise ValueError(REQUEST_ID_NOT_PROVIDED_ERROR)


def set_chat_type(data: chat_data) -> str:
    chat_type = data.get("type")
    chat_users = data.get("users", [])

    if not chat_type:
        if len(chat_users == 0) or len(chat_users >= 2):
            return Chat.Type.GROUP
        else:
            return Chat.Type.PERSNAL
    return chat_type


def create_chat(data: chat_data) -> chat_data:
    users = data.get("users", [])

    chat = Chat.objects.create(
        name=data['name'],
        author_id=data["author"],
        type=set_chat_type(data),
        users=[
            {
                "disabled": False,
                "user_id": user,
            }
            for user in users
        ]
    )
    return chat.get_all_data()


def create_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG)

    for data in consumer:

        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            new_chat_data = create_chat(data.value)
            create_chat_response_producer(
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=new_chat_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                )
            )
        except ValueError as err:
            create_chat_response_producer(
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                )
            )
