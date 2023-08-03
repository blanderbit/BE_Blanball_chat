from typing import Any, Optional

from chat.decorators import set_required_fields
from chat.exceptions import (
    InvalidDataException,
    NotFoundException,
    PermissionsDeniedException,
)
from chat.models import Chat, Messsage
from chat.serializers import (
    MessagesListSerializer,
)
from chat.tasks.create_chat import create_chat
from chat.utils import (
    check_user_is_chat_member,
    get_chat,
    get_message,
    get_request_for_chat_without_error,
    remove_unnecessary_data,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "create_message"

CANT_SEND_MESSAGE_IN_DISABLED_CHAT_ERROR: str = "cant_send_message_in_disabled_chat"
YOU_CANT_SEND_MESSSAGE_TO_YOUR_SELF_ERROR: str = "cant_send_message_to_your_self"
MUST_BE_PROVIDED_CHAT_ID_OR_USER_ID_FOR_REQUEST_CHAT_ERROR: str = (
    "must_be_provided_chat_id_or_user_id_for_request_chat"
)


CREATE_MESSAGE_FIELDS: list[str] = ["sender_id", "text", "reply_to"]

MESSAGE_TYPES: dict[str, str] = {"n_r": "new_request_for_chat", "c_m": "create_message"}

message_data = dict[str, Any]


@set_required_fields(
    ["request_user_id", "text", ["chat_id", "user_id_for_request_chat"]]
)
def validate_input_data(data: message_data) -> None:
    request_user_id: int = data.get("request_user_id")
    user_id_for_request_chat: Optional[int] = data.get("user_id_for_request_chat")
    chat_id: Optional[int] = data.get("chat_id")
    reply_to_message_id: Optional[int] = data.get("reply_to_message_id")

    if (
        user_id_for_request_chat
        and request_user_id
        and request_user_id == user_id_for_request_chat
    ):
        raise PermissionsDeniedException(YOU_CANT_SEND_MESSSAGE_TO_YOUR_SELF_ERROR)
    if chat_id and user_id_for_request_chat:
        raise InvalidDataException(
            MUST_BE_PROVIDED_CHAT_ID_OR_USER_ID_FOR_REQUEST_CHAT_ERROR
        )

    chat_instance: Optional[Chat] = None
    message_type: str = MESSAGE_TYPES["c_m"]

    if user_id_for_request_chat:
        chat_instance = get_request_for_chat_without_error(
            user_id_for_request_chat=user_id_for_request_chat,
            request_user_id=request_user_id,
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

    return {"message_type": message_type, "chat": chat_instance}


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
        "message_data": MessagesListSerializer(message).data,
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
        "users": chat.users_in_the_chat,
        "chat_id": chat.id,
        "message_data": MessagesListSerializer(message).data,
    }

    if created_chat_data:
        response_data["request_for_chat_data"] = created_chat_data["chat_data"]

    return response_data


def create_service_message(
    *, message_data: message_data, chat: Optional[Chat]
) -> Messsage:
    message: Messsage = chat.messages.create(**message_data)
    return message
