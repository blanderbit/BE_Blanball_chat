from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    InvalidDataException,
    NotProvidedException,
)
from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    generate_response,
    add_request_data_to_response,
    round_date_and_time
)
from chat.decorators.set_required_fields import (
    set_required_fields
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "create_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "create_chat_response"

MESSAGE_TYPES: dict[str, str] = {
    Chat.Type.PERSONAL: "create_personal_chat",
    Chat.Type.GROUP: "create_group_or_event_group_chat",
    Chat.Type.EVENT_GROUP: "create_group_or_event_group_chat"
}

chat_data = dict[str, Any]


@set_required_fields(["name", "request_user_id"])
def validate_input_data(data: chat_data) -> None:
    pass


def set_chat_type(data: chat_data) -> str:
    type: Optional[str] = data.get("type")
    chat_users: list[Optional[int]] = data.get("users", [])
    event_id: Optional[int] = data.get("event_id")

    if not type:
        if len(chat_users) == 0 or len(chat_users) >= 2 and not data.get("user_id_for_request_chat"):
            type = Chat.Type.GROUP if not event_id else Chat.Type.EVENT_GROUP
        else:
            type = Chat.Type.PERSONAL
    elif type == Chat.Type.EVENT_GROUP and not event_id:
        raise NotProvidedException(fields=["event_id"])

    global message_type
    message_type = MESSAGE_TYPES[type]
    return type


def create_chat(data: chat_data, return_instance: bool = False) -> Optional[chat_data]:
    users: list[Optional[int]] = data.get("users", [])
    event_id: Optional[int] = data.get("event_id")
    users.append(data["request_user_id"])

    chat_type: str = set_chat_type(data)
    chat_name: Optional[str] = data.get("name")

    try:
        chat: Chat = Chat.objects.create(
            name=chat_name,
            type=chat_type,
            event_id=event_id,
            users=[
                Chat.create_user_data_before_add_to_chat(
                    is_author=user == data["request_user_id"] and chat_type != Chat.Type.PERSONAL,
                    is_chat_request=user == data.get("user_id_for_request_chat"),
                    user_id=user,
                )
                for user in users
            ],
        )

        chat.time_created = round_date_and_time(chat.time_created)
        chat.save()

        response_data: dict[str, Any] = {
            "users": chat.users,
            "chat_data": {
                "id": chat.id,
                "name": chat.name,
                "type": chat.type,
                "image": chat.image,
            },
        }

        if return_instance:
            response_data = {
                "chat_instance": chat,
                "chat_data": response_data["chat_data"]
            }

        return response_data

    except Exception as _err:
        print(_err)
        raise InvalidDataException


def process_create_chat_request(data: chat_data) -> None:
    try:
        validate_input_data(data)
        new_chat_data = create_chat(data)
        default_producer(
            RESPONSE_TOPIC_NAME,
            generate_response(
                status=RESPONSE_STATUSES["SUCCESS"],
                data=new_chat_data,
                message_type=message_type,
                request_data=add_request_data_to_response(data)
            ),
        )
    except COMPARED_CHAT_EXCEPTIONS as err:
        default_producer(
            RESPONSE_TOPIC_NAME,
            generate_response(
                status=RESPONSE_STATUSES["ERROR"],
                data=str(err),
                message_type=message_type,
                request_data=add_request_data_to_response(data)
            ),
        )


def create_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        process_create_chat_request(data.value)
