from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.decorators import set_required_fields
from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    InvalidDataException,
    NotFoundException,
    PermissionsDeniedException,
)
from chat.models import Chat, Messsage
from chat.serializers import (
    MessagesListSerializer,
)
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    add_request_data_to_response,
    check_user_is_chat_member,
    generate_response,
    get_message,
    remove_unnecessary_data,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "edit_message"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "edit_message_response"

CANT_EDIT_MESSAGE_IN_DISABLED_CHAT_ERROR: str = "cant_edit_message_in_disabled_chat"
TIME_TO_EDIT_THE_MESSAGE_EXPIRED_ERROR: str = "time_to_edit_the_message_expired"
YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_MESSAGE_ERROR: str = (
    "you_dont_have_permissions_to_edit_this_message"
)


EDIT_MESSAGE_FIELDS: list[str] = ["text"]

MESSAGE_TYPE: str = "edit_message"


message_data = dict[str, Any]


@set_required_fields(["request_user_id", "message_id"])
def validate_input_data(data: message_data) -> None:
    request_user_id: int = data.get("request_user_id")
    message_id: int = data.get("message_id")

    message_instance = get_message(message_id=message_id)
    chat_instance: Chat = message_instance.chat.first()

    if not check_user_is_chat_member(chat=chat_instance, user_id=request_user_id):
        raise NotFoundException(object="chat")

    if message_instance.sender_id != request_user_id:
        raise PermissionsDeniedException(
            YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_MESSAGE_ERROR
        )

    if message_instance.service:
        raise PermissionsDeniedException(
            YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_MESSAGE_ERROR
        )

    if chat_instance.disabled:
        raise PermissionsDeniedException(CANT_EDIT_MESSAGE_IN_DISABLED_CHAT_ERROR)

    if message_instance.is_expired_to_edit():
        raise PermissionsDeniedException(TIME_TO_EDIT_THE_MESSAGE_EXPIRED_ERROR)

    return {"message_instance": message_instance, "chat_instance": chat_instance}


def prepare_data_before_edit_message(*, data: message_data) -> message_data:
    prepared_data = remove_unnecessary_data(data, *EDIT_MESSAGE_FIELDS)

    return prepared_data


def edit_message(
    *, message: Messsage, new_data: message_data, chat: Chat
) -> Optional[str]:
    try:
        prepared_data = prepare_data_before_edit_message(data=new_data)

        message.__dict__.update(**prepared_data, edited=True)
        message.edited = True
        message.save()

        response_data: dict[str, Any] = {
            "users": chat.users_in_the_chat,
            "chat_id": chat.id,
            "message_data": MessagesListSerializer(message).data,
        }

        return response_data

    except Exception as _err:
        print(_err)
        raise InvalidDataException


def edit_message_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            valid_data = validate_input_data(data.value)
            response_data = edit_message(
                message=valid_data["message_instance"],
                chat=valid_data["chat_instance"],
                new_data=data.value["new_data"],
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
