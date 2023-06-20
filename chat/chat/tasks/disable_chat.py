from typing import Any, Optional, Union

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    NotProvidedException,
)
from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    generate_response,
    get_chat,
    prepare_response,
    add_request_data_to_response
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "disable_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "disable_chat_response"

MESSAGE_TYPE: str = "disable_chat"


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    chat_id: Optional[int] = data.get("chat_id")
    event_id: Optional[int] = data.get("event_id")

    if not event_id and not chat_id:
        raise NotProvidedException(fields=["event_id", "chat_id"])

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id)


def disable_chat(*, chat: Chat) -> None:
    chat.disabled = True
    chat.save()

    response_data: dict[str, Union[int, list[int]]] = {
        "users": chat.users,
        "chat_id": chat.id,
    }

    return prepare_response(data=response_data, keys_to_keep=["users"])


def disable_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            validate_input_data(data.value)
            response_data = disable_chat(
                user_id=data.value.get("user_id"), chat=chat_instance
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
                    data=prepare_response(data=str(err)),
                    message_type=MESSAGE_TYPE,
                    request_data=add_request_data_to_response(data.value)
                ),
            )
