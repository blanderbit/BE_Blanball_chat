from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    PermissionsDeniedException,
)
from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_in_chat,
    check_user_is_chat_author,
    find_user_in_chat_by_id,
    generate_response,
    get_chat,
    add_request_data_to_response
)
from chat.decorators import (
    set_required_fields
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "remove_user_from_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "remove_user_from_chat_response"

MESSAGE_TYPE: str = "remove_user_from_chat"

CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT: str = "cant_remove_user_who_not_in_the_chat"
YOU_DONT_HAVE_PERMISSIONS_TO_REMOVE_USER_FROM_THIS_CHAT_ERROR: str = (
    "you_dont_have_permissions_to_remove_user_from_this_chat"
)
CANT_REMOVE_USER_FROM_PERSONAL_CHAT: str = "cant_remove_user_from_personal_chat"


chat_data = dict[str, Any]


@set_required_fields(["user_id", ["chat_id", "event_id"]])
def validate_input_data(data: chat_data) -> None:
    user_id: int = data.get("user_id")
    chat_id: Optional[int] = data.get("chat_id")
    event_id: Optional[int] = data.get("event_id")
    request_user_id: Optional[int] = data.get("request_user_id")

    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if request_user_id:
        if chat_instance.type == Chat.Type.PERSONAL:
            raise PermissionsDeniedException(CANT_REMOVE_USER_FROM_PERSONAL_CHAT)

        if not check_user_is_chat_author(chat=chat_instance, user_id=request_user_id):
            raise PermissionsDeniedException(
                YOU_DONT_HAVE_PERMISSIONS_TO_REMOVE_USER_FROM_THIS_CHAT_ERROR
            )

    if not check_user_in_chat(chat=chat_instance, user_id=user_id):
        raise PermissionsDeniedException(CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT)

    return {
        "chat_instance": chat_instance
    }


def remove_user_from_chat(
    *, user_id: int, chat: Chat, request_user_id: Optional[int] = None
) -> str:
    user_to_remove = find_user_in_chat_by_id(users=chat.users, user_id=user_id)

    if user_to_remove:
        if (
            chat.type == Chat.Type.GROUP or chat.type == Chat.Type.EVENT_GROUP
        ) and request_user_id:
            user_to_remove["removed"] = True
        else:
            chat.users.remove(user_to_remove)
        chat.save()
    if len(chat.users) == 0:
        chat.delete()

    response_data: dict[str, Any] = {
        "users": chat.users,
        "chat_id": chat.id,
        "removed_user_id": user_id,
    }

    return response_data


def remove_user_from_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:

        try:
            valid_data = validate_input_data(data.value)
            response_data = remove_user_from_chat(
                user_id=data.value.get("user_id"),
                chat=valid_data["chat_instance"],
                request_user_id=data.value.get("request_user_id"),
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
