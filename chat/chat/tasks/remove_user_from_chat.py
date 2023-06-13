from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.exceptions import (
    NotProvidedException,
    PermissionsDeniedException,
    COMPARED_CHAT_EXCEPTIONS,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_is_chat_author,
    check_user_in_chat,
    find_user_in_chat_by_id,
    generate_response,
    get_chat,
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


def validate_input_data(data: chat_data) -> None:
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    event_id = data.get("event_id")
    sender_user_id = data.get("sender_user_id")

    if not user_id:
        raise NotProvidedException(fields=["user_id"])
    if not event_id and not chat_id:
        raise NotProvidedException(fields=["event_id", "chat_id"])

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if sender_user_id:
        if chat_instance.type == Chat.Type.PERSONAL:
            raise PermissionsDeniedException(CANT_REMOVE_USER_FROM_PERSONAL_CHAT)

        if not check_user_is_chat_author(chat=chat_instance, user_id=sender_user_id):
            raise PermissionsDeniedException(
                YOU_DONT_HAVE_PERMISSIONS_TO_REMOVE_USER_FROM_THIS_CHAT_ERROR
            )

    if not check_user_in_chat(chat=chat_instance, user_id=user_id):
        raise PermissionsDeniedException(CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT)


def remove_user_from_chat(
    *, user_id: int, chat: Chat, sender_user_id: Optional[int] = None
) -> str:
    user_to_remove = find_user_in_chat_by_id(users=chat.users, user_id=user_id)

    if user_to_remove:
        if (
            chat.type == Chat.Type.GROUP or chat.type == Chat.Type.EVENT_GROUP
        ) and sender_user_id:
            user_to_remove["removed"] = True
        else:
            chat.users.remove(user_to_remove)
        chat.save()
    if len(chat_instance.users) == 0:
        chat.delete()

    return {
        "chat_id": chat.id,
        "users": chat.users,
        "removed_user": user_id
    }


def remove_user_from_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = remove_user_from_chat(
                user_id=data.value.get("user_id"),
                chat=chat_instance,
                sender_user_id=data.value.get("sender_user_id"),
            )
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id,
                ),
            )
        except COMPARED_CHAT_EXCEPTIONS as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id,
                ),
            )
