from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.errors import (
    CHAT_NOT_FOUND_ERROR,
)
from chat.exceptions import (
    NotProvidedException
)
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    generate_response,
    custom_pagination,
    get_chat,
    check_user_in_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chat_messages_list"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "get_chat_messages_list_response"

MESSAGE_TYPE: str = "get_chat_messages_list"

MESSAGE_FIELDS_TO_SERIALIZE: list[str] = [
    "id",
    "sender_id",
    "text",
    "string_time_created",
    "readed_by",
    "disabled",
    "edited"
]

chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    user_id: int = data.get("user_id")
    chat_id: int = data.get("chat_id")

    if not user_id:
        raise NotProvidedException(fields=["user_id"])
    if not chat_id:
        raise NotProvidedException(fields=["chat_id"])

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_in_chat(chat=chat_instance, user_id=user_id):
        raise ValueError(CHAT_NOT_FOUND_ERROR)


def get_chat_messages_list(*, data: chat_data) -> None:
    offset: int = data.get("offset", 10)
    page: int = data.get("page", 1)
    search: Optional[str] = data.get("search")

    queryset = chat_instance.messages.all()

    if search:
        queryset = queryset.filter(text__icontains=search)

    return custom_pagination(
        queryset=queryset,
        offset=offset,
        page=page,
        fields=MESSAGE_FIELDS_TO_SERIALIZE
    )


def get_chat_messages_list_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")
        try:
            validate_input_data(data.value)
            response_data = get_chat_messages_list(
                data=data.value
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
