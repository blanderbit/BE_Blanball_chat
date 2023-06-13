from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    NotProvidedException,
    PermissionsDeniedException,
)
from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_is_chat_member,
    generate_response,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "add_user_to_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "add_user_to_chat_response"

MESSAGE_TYPE: str = "add_user_to_chat"

CANT_ADD_USER_TO_PERSONAL_CHAT_ERROR: str = "cant_add_user_to_personal_chat"
CANT_ADD_USER_WHO_IS_ALREADY_IN_THE_CHAT_ERROR: str = (
    "cant_add_user_who_is_already_in_the_chat"
)
LIMIT_OF_USERS_REACHED_ERROR: str = "limit_of_users_{limit}_reached"


def validate_input_data(data: dict[str, int]) -> None:
    user_id: Optional[int] = data.get("user_id")
    event_id: Optional[int] = data.get("event_id")
    chat_id: Optional[int] = data.get("chat_id")

    if not user_id:
        raise NotProvidedException(fields=["user_id"])
    if not event_id and not chat_id:
        raise NotProvidedException(fields=["event_id", "chat_id"])

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if len(chat_instance.users) >= chat_instance.chat_users_count_limit:
        raise PermissionsDeniedException(
            LIMIT_OF_USERS_REACHED_ERROR.format(
                limit=chat_instance.chat_users_count_limit
            )
        )
    if chat_instance.type == Chat.Type.PERSONAL:
        raise PermissionsDeniedException(CANT_ADD_USER_TO_PERSONAL_CHAT_ERROR)
    elif check_user_is_chat_member(chat=chat_instance, user_id=user_id):
        raise PermissionsDeniedException(CANT_ADD_USER_WHO_IS_ALREADY_IN_THE_CHAT_ERROR)


def add_user_to_chat(user_id: int, chat: Chat) -> str:
    chat.users.append(
        Chat.create_user_data_before_add_to_chat(
            is_author=False,
            user_id=user_id,
        )
    )
    chat.save()

    return {"chat_id": chat.id, "users": chat.users, "new_user": user_id}


def add_user_to_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")
        try:
            validate_input_data(data.value)
            response_data = add_user_to_chat(
                user_id=data.value.get("user_id"), chat=chat_instance
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
