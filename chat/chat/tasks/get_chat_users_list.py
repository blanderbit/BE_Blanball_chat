from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    NotFoundException,
)
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_in_chat,
    custom_json_field_pagination,
    generate_response,
    add_request_data_to_response,
    get_chat,
)
from chat.decorators import (
    set_required_fields
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chat_users_list"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "get_chat_users_list_response"

MESSAGE_TYPE: str = "get_chat_users_list"


@set_required_fields(["request_user_id", "chat_id"])
def validate_input_data(data: dict[str, int]) -> None:
    request_user_id: int = data.get("request_user_id")
    chat_id: int = data.get("chat_id")

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_in_chat(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")


def get_chat_users_list(*, data: dict[str, int]) -> dict[str, Any]:
    offset: int = data.get("offset", 10)
    page: int = data.get("page", 1)

    return custom_json_field_pagination(
        model_instance=chat_instance,
        page=page,
        offset=offset,
        field_name="users",
    )


def get_chat_users_list_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            validate_input_data(data.value)
            response_data = get_chat_users_list(data=data.value)
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
