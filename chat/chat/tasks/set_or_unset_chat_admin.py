from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
    NotProvidedException,
    PermissionsDeniedException,
    InvalidDataException,
)
from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    generate_response,
    get_chat,
    check_user_is_chat_author,
    check_user_is_chat_member,
    check_user_is_chat_admin,
    prepare_response,
    add_request_data_to_response
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "set_or_unset_chat_admin_admin"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "set_or_unset_chat_admin_response"
CANT_SET_OR_UNSET_ADMIN_IN_PERSONAL_CHAT_ERROR: str = "cant_{action}_admin_in_personal_chat"
CANT_SET_OR_UNSET_ADMIN_WHO_IS_NOT_IN_THE_CHAT_ERROR: str = "cant_{action}_admin_who_not_in_the_chat"
CANT_SET_OR_UNSET_ADMIN_WHO_IS_ALREADY_ADMIN_ERROR: str = "cant_{action}_admin_who_is_already_admin"
CANT_SET_OR_UNSET_ADMIN_WHO_IS_AUTHOR_ERROR: str = "cant_{action}_admin_who_is_author"
CANT_SET_OR_UNSET_ADMIN_IN_DISABLED_CHAT_ERROR: str = "cant_{action}_admin_in_disabled_chat"
LIMIT_OF_ADMINS_REACHED_ERROR: str = "limit_of_admins_{limit}_reached"
ACTION_INVALID_ERROR: str = "action_invalid"

MESSAGE_TYPE: str = "set_or_unset_chat_admin_admin"

ACTION_OPTIONS: dict[str, str] = {"set": "set", "unset": "unset"}


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    chat_id: Optional[int] = data.get("chat_id")
    author_id: Optional[int] = data.get("author_id")
    user_id: Optional[int] = data.get("user_id")
    action: Optional[str] = data.get("action")

    if not action:
        raise NotProvidedException(fields=["action"])
    if action not in ACTION_OPTIONS:
        raise InvalidDataException(ACTION_INVALID_ERROR)

    if not chat_id:
        raise NotProvidedException(fields=["chat_id"])
    if not author_id:
        raise NotProvidedException(fields=["author_id"])
    if not user_id:
        raise NotProvidedException(fields=["user_id"])

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id)

    check_author_permissions(chat_instance, author_id)
    check_member_permissions(chat_instance, user_id, action)

    if chat_instance.disabled:
        raise PermissionsDeniedException(CANT_SET_OR_UNSET_ADMIN_IN_DISABLED_CHAT_ERROR.format(action=action))

    if chat_instance.type == Chat.Type.PERSONAL:
        raise PermissionsDeniedException(CANT_SET_OR_UNSET_ADMIN_IN_PERSONAL_CHAT_ERROR.format(action=action))

    if len(chat_instance.chat_admins) >= chat_instance.chat_admins_count_limit:
        raise PermissionsDeniedException(LIMIT_OF_ADMINS_REACHED_ERROR.format(limit=chat_instance.chat_admins_count_limit))


def check_author_permissions(chat: Chat, author_id: int) -> None:
    if not check_user_is_chat_author(chat, author_id):
        raise PermissionsDeniedException()


def check_member_permissions(chat: Chat, user_id: int, action: str) -> None:
    if not check_user_is_chat_member(chat, user_id):
        raise PermissionsDeniedException(CANT_SET_OR_UNSET_ADMIN_WHO_IS_NOT_IN_THE_CHAT_ERROR.format(action=action))

    if check_user_is_chat_author(chat, user_id):
        raise PermissionsDeniedException(CANT_SET_OR_UNSET_ADMIN_WHO_IS_AUTHOR_ERROR.format(action=action))

    if check_user_is_chat_admin(chat, user_id):
        raise PermissionsDeniedException(CANT_SET_OR_UNSET_ADMIN_WHO_IS_ALREADY_ADMIN_ERROR.format(action=action))


def set_or_unset_chat_admin(*, chat: Chat, user_id: int, action: str) -> None:
    user = [user for user in chat.users if user.get("user_id") == user_id][0]
    if action == ACTION_OPTIONS["set"]:
        user["admin"] = True
    else:
        user["admin"] = False
    chat.save()

    response_data: dict[str, Any] = {
        "users": chat.users,
        "chat_id": chat.id,
        "new_admin_id": user_id,
    }

    return prepare_response(data=response_data, keys_to_keep=["users"])


def set_or_unset_chat_admin_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        try:
            validate_input_data(data.value)
            response_data = set_or_unset_chat_admin(
                chat=chat_instance,
                user_id=data.value["user_id"],
                action=data.value["action"]
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
                    data=prepare_response(data=str(err)),
                    message_type=MESSAGE_TYPE,
                    request_data=add_request_data_to_response(data.value)
                ),
            )
