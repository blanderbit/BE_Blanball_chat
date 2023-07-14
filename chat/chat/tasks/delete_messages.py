from typing import Any, Optional

from django.conf import settings
from django.db.models.query import QuerySet
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
)
from chat.models import Messsage, Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.exceptions import (
    NotFoundException
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_is_chat_member,
    generate_response,
    add_request_data_to_response,
    get_chat,
    check_user_in_chat,
)
from chat.decorators import (
    set_required_fields,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "delete_messages"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "delete_messages_response"

MESSAGE_TYPE: str = "delete_messages"


message_data = dict[str, Any]


@set_required_fields(["message_ids", "request_user_id", "chat_id"])
def validate_input_data(data: message_data) -> None:
    request_user_id: int = data.get("request_user_id")
    chat_id: int = data.get("chat_id")
    message_ids: list[Optional[int]] = data.get("message_ids")

    chat_instance = get_chat(chat_id=chat_id)

    if not check_user_in_chat(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    messages: QuerySet[Messsage] = chat_instance.messages.filter(id__in=message_ids)
    messages_objects: list[Optional[Messsage]] = []

    for message in messages:
        if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
            return None
        if chat_instance.disabled:
            return None
        if request_user_id != message.sender_id:
            return None
        if message.service:
            return None
        messages_objects.append(message)
    return {
        "messages_objects": messages_objects,
        "chat_instance": chat_instance
    }


def delete_messages(*, messages: QuerySet[Messsage], chat: Chat) -> list[Optional[int]]:
    success: list[Optional[int]] = []
    for message_obj in messages:
        message_id = message_obj.id
        message_obj.delete()
        success.append(message_id)
    return {
        "users": chat.users,
        "chat_id": chat.id,
        "messages_ids": success
    }


def delete_messages_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:

        try:
            valid_data = validate_input_data(data.value)
            response_data = delete_messages(
                messages=valid_data["messages_objects"],
                chat=valid_data["chat_instance"],
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
