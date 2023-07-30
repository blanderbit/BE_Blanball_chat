from typing import Any, Optional, Union

from django.conf import settings
from kafka import KafkaConsumer

from chat.decorators import set_required_fields
from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    PermissionsDeniedException,
)
from chat.models import Chat, Messsage
from chat.serializers import (
    ServiceMessageSeralizer,
)
from chat.tasks.create_message import (
    create_service_message,
)
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    add_request_data_to_response,
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
CANT_ADD_USER_TO_DISABLED_CHAT_ERROR: str = "cant_add_user_to_disabled_chat"
CANT_ADD_USER_WHO_IS_ALREADY_IN_THE_CHAT_ERROR: str = (
    "cant_add_user_who_is_already_in_the_chat"
)
LIMIT_OF_USERS_REACHED_ERROR: str = "limit_of_users_{limit}_reached"


@set_required_fields(["user_id", ["event_id", "chat_id"]])
def validate_input_data(data: dict[str, int]) -> None:
    user_id: int = data.get("user_id")
    event_id: Optional[int] = data.get("event_id")
    chat_id: Optional[int] = data.get("chat_id")

    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if check_user_is_chat_member(chat=chat_instance, user_id=user_id):
        raise PermissionsDeniedException(CANT_ADD_USER_WHO_IS_ALREADY_IN_THE_CHAT_ERROR)

    if len(chat_instance.users_in_the_chat) >= chat_instance.chat_users_count_limit:
        raise PermissionsDeniedException(
            LIMIT_OF_USERS_REACHED_ERROR.format(
                limit=chat_instance.chat_users_count_limit
            )
        )
    if chat_instance.type == Chat.Type.PERSONAL:
        raise PermissionsDeniedException(CANT_ADD_USER_TO_PERSONAL_CHAT_ERROR)

    if chat_instance.disabled:
        raise PermissionsDeniedException(CANT_ADD_USER_TO_DISABLED_CHAT_ERROR)

    return {"chat_instance": chat_instance}


def add_user_to_chat(user_id: int, chat: Chat) -> str:
    new_service_message: Optional[Messsage] = None

    chat.users.append(
        Chat.create_user_data_before_add_to_chat(
            is_author=False,
            user_id=user_id,
        )
    )
    chat.save()

    if chat.is_group:
        new_service_message = create_service_message(
            message_data={
                "type": Messsage.Type.USER_JOINED_TO_CHAT,
                "sender_id": user_id,
            },
            chat=chat,
        )

    response_data: dict[str, Union[int, list[int]]] = {
        "chat_id": chat.id,
        "users": chat.users_in_the_chat,
        "new_user_id": user_id,
    }

    if new_service_message:
        response_data["service_message"] = ServiceMessageSeralizer(
            new_service_message
        ).data

    return response_data


def add_user_to_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            valid_data = validate_input_data(data.value)
            response_data = add_user_to_chat(
                user_id=data.value.get("user_id"), chat=valid_data["chat_instance"]
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
