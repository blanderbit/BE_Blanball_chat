from typing import Any, Optional

from django.conf import settings
from django.db.models import Q
from kafka import KafkaConsumer

from chat.decorators import set_required_fields
from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
)
from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    add_request_data_to_response,
    generate_response,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chats_count"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "get_chats_count_response"

MESSAGE_TYPE: str = "get_chats_count"


@set_required_fields(["request_user_id"])
def validate_input_data(data: dict[str, int]) -> None:
    pass


def get_chats_count(*, data: dict[str, int]) -> dict[str, int]:
    request_user_id = data["request_user_id"]

    all_chats_count: int = 0
    personal_chats_count: int = 0
    group_chats_count: int = 0
    chat_requests_count: int = 0

    all_users_chats = Chat.get_only_available_chats_for_user_without_sortering(
        request_user_id
    )

    if len(all_users_chats) > 0:
        all_chats_count = all_users_chats.count()
        personal_chats_count = all_users_chats.filter(type=Chat.Type.PERSONAL).count()
        group_chats_count = all_users_chats.filter(
            type__in=Chat.CHAT_GROUP_TYPES()
        ).count()
        chat_requests_count = all_users_chats.filter(
            users__contains=[
                {
                    "user_id": request_user_id,
                    "chat_request": True,
                }
            ]
        ).count()

    chats_count_info: dict[str, int] = {
        "all_chats_count": all_chats_count,
        "personal_chats_count": personal_chats_count,
        "group_chats_count": group_chats_count,
        "chat_requests_count": chat_requests_count,
    }

    return chats_count_info


def get_chats_count_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            validate_input_data(data.value)
            response_data = get_chats_count(
                data=data.value,
            )
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_data=add_request_data_to_response(data.value),
                ),
            )
        except COMPARED_CHAT_EXCEPTIONS as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_data=add_request_data_to_response(data.value),
                ),
            )
