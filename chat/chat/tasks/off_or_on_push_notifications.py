from typing import Any

from django.conf import settings
from kafka import KafkaConsumer

from chat.decorators.set_required_fields import (
    set_required_fields,
)
from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    InvalidActionException,
    NotFoundException,
)
from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    add_request_data_to_response,
    check_user_is_chat_member,
    find_user_in_chat_by_id,
    generate_response,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "off_or_on_push_notifications"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "off_or_on_push_notifications_response"

MESSAGE_TYPE: str = "off_or_on_push_notifications"

ACTION_OPTIONS: dict[str, str] = {"on": "on", "off": "off"}


@set_required_fields(["request_user_id", "chat_id", "action"])
def validate_input_data(data: dict[str, Any]) -> None:
    request_user_id: int = data.get("request_user_id")
    action: str = data.get("action")
    chat_id: int = data.get("chat_id")

    chat_instance = get_chat(chat_id=chat_id)

    if action not in ACTION_OPTIONS:
        raise InvalidActionException

    if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    return {"chat_instance": chat_instance}


def off_or_on_push_notifications(*, request_data: dict[str, Any], chat: Chat) -> None:
    user_id: int = request_data["request_user_id"]
    action: str = request_data["action"]

    user_to_remove = find_user_in_chat_by_id(users=chat.users, user_id=user_id)

    user_to_remove["push_notifications"] = action == ACTION_OPTIONS["on"]

    chat.save()

    response_data: dict[str, Any] = {
        "chat_id": chat.id,
        "action": action,
    }

    return response_data


def off_or_on_push_notifications_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            valid_data = validate_input_data(data.value)
            response_data = off_or_on_push_notifications(
                request_data=data.value, chat=valid_data["chat_instance"]
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
