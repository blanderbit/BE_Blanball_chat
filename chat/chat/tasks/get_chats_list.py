from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    NotProvidedException,
)
from chat.models import Chat
from chat.serializers import ChatsListSerializer
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    custom_pagination,
    generate_response,
    prepare_response,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chats_list"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "get_chats_list_response"

MESSAGE_TYPE: str = "get_chats_list"


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    user_id: int = data.get("user_id")

    if not user_id:
        raise NotProvidedException(fields=["user_id"])


def get_chats_list(*, data: chat_data) -> dict[str, Any]:
    user_id: Optional[int] = data.get("user_id")
    offset: int = data.get("offset", 10)
    page: int = data.get("page", 1)
    search: Optional[str] = data.get("search")

    queryset = Chat.get_only_available_chats_for_user(user_id=user_id)

    if search:
        queryset = Chat.get_only_available_chats_for_user(user_id=user_id).filter(
            name__icontains=search
        )

    return prepare_response(
        data=custom_pagination(
            queryset=queryset,
            offset=offset,
            page=page,
            serializer_class=ChatsListSerializer,
        ))


def get_chats_list_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")
        try:
            validate_input_data(data.value)
            response_data = get_chats_list(data=data.value)
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
