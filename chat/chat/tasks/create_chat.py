from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    generate_response,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "create_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "create_chat_response"
CHAT_NAME_NOT_PROVIDED_ERROR: str = "name_not_provided"
CHAT_AUTOR_NOT_PROVIDED_ERROR: str = "author_not_provided"
REQUEST_ID_NOT_PROVIDED_ERROR: str = "request_id_not_provided"
CHAT_EVENT_ID_NOT_PROVIDED: str = "event_id_not_provided"
PROVIDED_DATA_INVALID_TO_CREATE_THE_CHAT_ERROR: str = "provided_data_invalid_to_create_the_chat"

MESSAGE_TYPE: str = "create_chat"


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    name: Optional[str] = data.get("name")
    author: Optional[str] = data.get("author")

    if not name:
        raise ValueError(CHAT_NAME_NOT_PROVIDED_ERROR)
    if not author:
        raise ValueError(CHAT_AUTOR_NOT_PROVIDED_ERROR)


def set_chat_type(data: chat_data) -> str:
    chat_type = data.get("type")
    chat_users = data.get("users", [])
    event_id = data.get("event_id")

    if not chat_type:
        if len(chat_users == 0) or len(chat_users >= 2):
            if not event_id:
                return Chat.Type.GROUP
            return Chat.Type.EVENT_GROUP
        else:
            return Chat.Type.PERSONAL
    elif chat_type == Chat.Type.EVENT_GROUP and not event_id:
        raise ValueError(CHAT_EVENT_ID_NOT_PROVIDED)
    return chat_type


def create_chat(data: chat_data) -> Optional[chat_data]:
    users = data.get("users", [])
    event_id = data.get("event_id")
    users.append(data["author"])
    if data.get("user"):
        users.append(data.get("user"))
    try:
        chat = Chat.objects.create(
            name=data["name"],
            type=set_chat_type(data),
            event_id=event_id,
            users=[
                Chat.create_user_data_before_add_to_chat(
                    is_author=user == data["author"],
                    user_id=user,
                )
                for user in users
            ],
        )
        return chat.get_all_data()
    except Exception:
        raise ValueError(PROVIDED_DATA_INVALID_TO_CREATE_THE_CHAT_ERROR)


def create_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            new_chat_data = create_chat(data.value)
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=new_chat_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id,
                ),
            )
        except ValueError as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id,
                ),
            )
