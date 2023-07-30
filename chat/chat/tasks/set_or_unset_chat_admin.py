from typing import Any

from django.conf import settings
from kafka import KafkaConsumer

from chat.decorators import set_required_fields
from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    InvalidActionException,
    PermissionsDeniedException,
)
from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    add_request_data_to_response,
    check_user_is_chat_admin,
    check_user_is_chat_author,
    check_user_is_chat_member,
    generate_response,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "set_or_unset_chat_admin"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "set_or_unset_chat_admin_response"
CANT_SET_OR_UNSET_ADMIN_IN_PERSONAL_CHAT_ERROR: str = (
    "cant_{action}_admin_in_personal_chat"
)
CANT_SET_OR_UNSET_ADMIN_WHO_IS_NOT_IN_THE_CHAT_ERROR: str = (
    "cant_{action}_admin_who_not_in_the_chat"
)
CANT_SET_ADMIN_WHO_IS_ALREADY_ADMIN_ERROR: str = "cant_set_admin_who_is_already_admin"
CANT_UNSET_ADMIN_WHO_IS_NOT_ADMIN_ERROR: str = "cant_set_admin_who_is_not_admin"
CANT_SET_OR_UNSET_ADMIN_WHO_IS_AUTHOR_ERROR: str = "cant_{action}_admin_who_is_author"
CANT_SET_OR_UNSET_ADMIN_IN_DISABLED_CHAT_ERROR: str = (
    "cant_{action}_admin_in_disabled_chat"
)
LIMIT_OF_ADMINS_REACHED_ERROR: str = "limit_of_admins_{limit}_reached"

MESSAGE_TYPE: str = "set_or_unset_chat_admin"

ACTION_OPTIONS: dict[str, str] = {"set": "set", "unset": "unset"}


chat_data = dict[str, Any]


@set_required_fields(["action", "chat_id", "request_user_id", "user_id"])
def validate_input_data(data: chat_data) -> None:
    chat_id: int = data.get("chat_id")
    request_user_id: int = data.get("request_user_id")
    user_id: int = data.get("user_id")
    action: str = data.get("action")

    if action not in ACTION_OPTIONS:
        raise InvalidActionException

    chat_instance = get_chat(chat_id=chat_id)

    check_author_permissions(chat_instance, request_user_id)
    check_member_permissions(chat_instance, user_id, action)

    if chat_instance.disabled:
        raise PermissionsDeniedException(
            CANT_SET_OR_UNSET_ADMIN_IN_DISABLED_CHAT_ERROR.format(action=action)
        )

    if chat_instance.type == Chat.Type.PERSONAL:
        raise PermissionsDeniedException(
            CANT_SET_OR_UNSET_ADMIN_IN_PERSONAL_CHAT_ERROR.format(action=action)
        )

    if (
        len(chat_instance.chat_admins) >= chat_instance.chat_admins_count_limit
        and action == ACTION_OPTIONS["set"]
    ):
        raise PermissionsDeniedException(
            LIMIT_OF_ADMINS_REACHED_ERROR.format(
                limit=chat_instance.chat_admins_count_limit
            )
        )

    return {"chat_instance": chat_instance}


def check_author_permissions(chat: Chat, request_user_id: int) -> None:
    if not check_user_is_chat_author(chat=chat, user_id=request_user_id):
        raise PermissionsDeniedException


def check_member_permissions(chat: Chat, user_id: int, action: str) -> None:
    if not check_user_is_chat_member(chat=chat, user_id=user_id):
        raise PermissionsDeniedException(
            CANT_SET_OR_UNSET_ADMIN_WHO_IS_NOT_IN_THE_CHAT_ERROR.format(action=action)
        )

    if check_user_is_chat_author(chat=chat, user_id=user_id):
        raise PermissionsDeniedException(
            CANT_SET_OR_UNSET_ADMIN_WHO_IS_AUTHOR_ERROR.format(action=action)
        )

    if (
        check_user_is_chat_admin(chat=chat, user_id=user_id)
        and action == ACTION_OPTIONS["set"]
    ):
        raise PermissionsDeniedException(CANT_SET_ADMIN_WHO_IS_ALREADY_ADMIN_ERROR)

    if (
        not check_user_is_chat_admin(chat=chat, user_id=user_id)
        and action == ACTION_OPTIONS["unset"]
    ):
        raise PermissionsDeniedException(CANT_UNSET_ADMIN_WHO_IS_NOT_ADMIN_ERROR)


def set_or_unset_chat_admin(*, chat: Chat, user_id: int, action: str) -> None:
    user = [user for user in chat.users if user.get("user_id") == user_id][0]
    user["admin"] = action == ACTION_OPTIONS["set"]
    chat.save()

    response_data: dict[str, Any] = {
        "users": chat.users_in_the_chat,
        "chat_id": chat.id,
        "action": action,
        "user_id": user_id,
    }

    return response_data


def set_or_unset_chat_admin_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            valid_data = validate_input_data(data.value)
            response_data = set_or_unset_chat_admin(
                chat=valid_data["chat_instance"],
                user_id=data.value["user_id"],
                action=data.value["action"],
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
