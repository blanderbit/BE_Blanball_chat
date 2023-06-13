from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.tasks.default_producer import (
    default_producer,
)
from chat.errors import (
    CHAT_NOT_FOUND_ERROR,
    PROVIDED_INVALID_DATA_ERROR,
)
from chat.exceptions import (
    NotProvidedException
)
from chat.utils import (
    RESPONSE_STATUSES,
    generate_response,
    get_chat,
    remove_unnecessary_data,
    check_user_is_chat_member,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "create_message"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "create_message_response"

CANT_SEND_MESSAGE_IN_DISABLED_CHAT_ERROR: str = "cant_send_message_in_disabled_chat"

CREATE_MESSAGE_FIELDS: list[str] = ["sender_id", "text", "chat"]

MESSAGE_TYPE: str = "create_message"


message_data = dict[str, Any]


def validate_input_data(data: message_data) -> None:
    user_id: Optional[int] = data.get("user_id")
    chat_id: Optional[int] = data.get("chat_id")
    message_text: Optional[str] = data.get("text")

    if not chat_id:
        raise NotProvidedException(fields=["chat_id"])
    if not user_id:
        raise NotProvidedException(fields=["user_id"])
    if not message_text:
        raise NotProvidedException(fields=["message_text"])

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_is_chat_member(chat=chat_instance, user_id=user_id):
        raise ValueError(CHAT_NOT_FOUND_ERROR)

    if chat_instance.disabled:
        raise ValueError(CANT_SEND_MESSAGE_IN_DISABLED_CHAT_ERROR)


def prepare_data_before_create_message(*, data: message_data) -> message_data:
    data["sender_id"] = data["user_id"]
    prepared_data = remove_unnecessary_data(
        data, *CREATE_MESSAGE_FIELDS
    )

    return prepared_data


def create_message(*, data: message_data) -> Optional[str]:
    try:
        prepared_data = prepare_data_before_create_message(data=data)
        message = chat_instance.messages.create(**prepared_data)

        return {
            "chat_id": chat_instance.id,
            "message_data": message.get_all_data(),
            "users": chat_instance.users
        }
    except Exception:
        raise ValueError(PROVIDED_INVALID_DATA_ERROR)


def create_message_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = create_message(
                data=data.value,
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
