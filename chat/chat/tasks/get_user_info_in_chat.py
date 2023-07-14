from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    NotFoundException,
)
from chat.models import (
    Chat
)
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_in_chat,
    generate_response,
    add_request_data_to_response,
    get_chat,
    find_user_in_chat_by_id,
)
from chat.decorators import (
    set_required_fields
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_user_info_in_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "get_user_info_in_chat_response"

MESSAGE_TYPE: str = "get_user_info_in_chat"


@set_required_fields(["request_user_id", "chat_id"])
def validate_input_data(data: dict[str, int]) -> None:
    request_user_id: int = data.get("request_user_id")
    chat_id: int = data.get("chat_id")

    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_in_chat(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    return {
        "chat_instance": chat_instance
    }


def get_user_info_in_chat(*, data: dict[str, int], chat: Chat) -> dict[str, Any]:
    request_user = find_user_in_chat_by_id(
        users=chat.users, user_id=data["request_user_id"]
    )

    user_info: dict[str, bool] = {
        "chat_id": chat.id,
        "author": request_user["author"],
        "disabled": request_user["disabled"],
        "admin": request_user["admin"],
        "chat_request": request_user["chat_request"],
        "push_notifications": request_user["push_notifications"]
    }

    return user_info


def get_user_info_in_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            valid_data = validate_input_data(data.value)
            response_data = get_user_info_in_chat(
                data=data.value,
                chat=valid_data["chat_instance"]
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
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_data=add_request_data_to_response(data.value)
                ),
            )
