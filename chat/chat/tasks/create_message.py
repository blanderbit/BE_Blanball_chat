from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    InvalidDataException,
    NotFoundException,
    PermissionsDeniedException,
)
from chat.models import (
    Messsage,
    Chat
)
from chat.tasks.default_producer import (
    default_producer,
)
from chat.tasks.create_chat import (
    create_chat
)
from chat.serializers import (
    MessagesListSerializer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_is_chat_member,
    generate_response,
    get_chat,
    get_message,
    remove_unnecessary_data,
    add_request_data_to_response,
    get_request_for_chat_without_error
)
from chat.decorators import (
    set_required_fields
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "create_message"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "create_message_response"

CANT_SEND_MESSAGE_IN_DISABLED_CHAT_ERROR: str = "cant_send_message_in_disabled_chat"
YOU_CANT_SEND_MESSSAGE_TO_YOUR_SELF_ERROR: str = "cant_send_message_to_your_self"
MUST_BE_PROVIDED_CHAT_ID_OR_USER_ID_FOR_REQUEST_CHAT_ERROR: str = "must_be_provided_chat_id_or_user_id_for_request_chat"


CREATE_MESSAGE_FIELDS: list[str] = ["sender_id", "text", "reply_to"]

MESSAGE_TYPES: dict[str, str] = {
    "n_r": "new_request_for_chat",
    "c_m": "create_message"
}

message_data = dict[str, Any]


@set_required_fields(["request_user_id", "text", ["chat_id", "user_id_for_request_chat"]])
def validate_input_data(data: message_data) -> None:
    request_user_id: int = data.get("request_user_id")
    user_id_for_request_chat: Optional[int] = data.get("user_id_for_request_chat")
    chat_id: Optional[int] = data.get("chat_id")
    reply_to_message_id: Optional[int] = data.get("reply_to_message_id")

    if user_id_for_request_chat and request_user_id and request_user_id == user_id_for_request_chat:
        raise PermissionsDeniedException(YOU_CANT_SEND_MESSSAGE_TO_YOUR_SELF_ERROR)
    if chat_id and user_id_for_request_chat:
        raise InvalidDataException(MUST_BE_PROVIDED_CHAT_ID_OR_USER_ID_FOR_REQUEST_CHAT_ERROR)

    chat_instance: Optional[Chat] = None
    message_type: str = MESSAGE_TYPES["c_m"]

    if user_id_for_request_chat:
        chat_instance = get_request_for_chat_without_error(
            user_id_for_request_chat=user_id_for_request_chat,
            request_user_id=request_user_id
        )
    else:
        chat_instance = get_chat(chat_id=chat_id)

    if chat_instance:
        if reply_to_message_id:
            if not chat_instance.messages.filter(id=reply_to_message_id).exists():
                raise NotFoundException(object="reply_to_message")

        if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
            raise NotFoundException(object="chat")

        if chat_instance.disabled:
            raise PermissionsDeniedException(CANT_SEND_MESSAGE_IN_DISABLED_CHAT_ERROR)
    else:
        message_type = MESSAGE_TYPES["n_r"]

    return {
        "message_type": message_type,
        "chat_instance": chat_instance
    }


def prepare_data_before_create_message(*, data: message_data) -> message_data:
    data["sender_id"] = data["request_user_id"]

    if data.get("reply_to_message_id"):
        data["reply_to"] = get_message(message_id=data["reply_to_message_id"])
    prepared_data = remove_unnecessary_data(data, *CREATE_MESSAGE_FIELDS)
    return prepared_data


def create_message(*, data: message_data, chat: Optional[Chat]) -> Optional[str]:
    created_chat_data: Optional[dict[str, Any]] = None

    if not chat:
        new_chat_data = {
            "request_user_id": data["request_user_id"],
            "user_id_for_request_chat": data["user_id_for_request_chat"],
            "users": [data["user_id_for_request_chat"]],
        }
        created_chat_data = create_chat(data=new_chat_data, return_instance=True)
        chat = created_chat_data.pop("chat_instance")
        data["chat_id"] = chat.id
    prepared_data = prepare_data_before_create_message(data=data)
    message: Messsage = chat.messages.create(**prepared_data)

    response_data: dict[str, Any] = {
        "users": chat.users,
        "chat_id": chat.id,
        "message_data": MessagesListSerializer(message).data
    }

    if created_chat_data:
        response_data["request_for_chat_data"] = created_chat_data["chat_data"]

    return response_data


def create_message(*, data: message_data, chat: Optional[Chat]) -> Optional[str]:
    created_chat_data: Optional[dict[str, Any]] = None

    if not chat:
        new_chat_data = {
            "request_user_id": data["request_user_id"],
            "user_id_for_request_chat": data["user_id_for_request_chat"],
            "users": [data["user_id_for_request_chat"]],
        }
        created_chat_data = create_chat(data=new_chat_data, return_instance=True)
        chat = created_chat_data.pop("chat_instance")
        data["chat_id"] = chat.id
    prepared_data = prepare_data_before_create_message(data=data)
    message: Messsage = chat.messages.create(**prepared_data)

    response_data: dict[str, Any] = {
        "users": chat.users,
        "chat_id": chat.id,
        "message_data": MessagesListSerializer(message).data
    }

    if created_chat_data:
        response_data["request_for_chat_data"] = created_chat_data["chat_data"]

    return response_data


def create_service_message(*, message_data: message_data, chat: Optional[Chat]) -> Messsage:
    message: Messsage = chat.messages.create(**message_data)
    return message


def create_message_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            valid_data = validate_input_data(data.value)
            response_data = create_message(
                data=data.value,
                chat=valid_data["chat_instance"]
            )
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=valid_data["message_type"],
                    request_data=add_request_data_to_response(data.value)
                ),
            )
        except COMPARED_CHAT_EXCEPTIONS as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=valid_data["message_type"],
                    request_data=add_request_data_to_response(data.value)
                ),
            )
