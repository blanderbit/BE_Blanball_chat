from typing import Any

from django.conf import settings
from kafka import KafkaConsumer, KafkaProducer

from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.tasks.utils import (
    RESPONSE_STATUSES,
    generate_response,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "add_user_to_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "add_user_to_chat_response"

MESSAGE_TYPE: str = "add_user_to_chat"

USER_ID_NOT_PROVIDED_ERROR: str = "user_id_not_provided"
CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR: str = "chat_id_or_event_id_not_provided"
CANT_ADD_USER_TO_PERSONAL_CHAT_ERROR: str = "cant_add_user_to_personal_chat"
CANT_ADD_USER_WHO_IS_ALREADY_IN_THE_CHAT_ERROR: str = (
    "cant_add_user_who_is_already_in_the_chat"
)

USER_ADDED_TO_CHAT_SUCCESS: dict[str, str] = "user_added_to_chat"

chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    user_id = data.get("user_id")
    event_id = data.get("event_id")
    chat_id = data.get("chat_id")

    if not user_id:
        raise ValueError(USER_ID_NOT_PROVIDED_ERROR)
    if not event_id and not chat_id:
        raise ValueError(CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR)

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if chat_instance.type == Chat.Type.PERSONAL:
        raise ValueError(CANT_ADD_USER_TO_PERSONAL_CHAT_ERROR)
    elif any(user["user_id"] == user_id for user in chat_instance.users):
        raise ValueError(CANT_ADD_USER_WHO_IS_ALREADY_IN_THE_CHAT_ERROR)


def add_user_to_chat(*, user_id: int, chat: Chat) -> str:
    chat.users.append(
        Chat.create_user_data_before_add_to_chat(
            is_author=False,
            user_id=user_id,
        )
    )
    chat.save()

    return USER_ADDED_TO_CHAT_SUCCESS


def add_user_to_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = add_user_to_chat(
                user_id=data.value.get("user_id"), chat=chat_instance
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
