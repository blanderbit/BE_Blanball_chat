from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.tasks.remove_user_from_chat import (
    remove_user_from_chat,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_is_all_users_deleted_personal_chat,
    check_user_is_chat_member,
    find_user_in_chat_by_id,
    generate_response,
    check_user_is_chat_admin,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "delete_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "delete_chat_response"

MESSAGE_TYPE: str = "delete_chat"


CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR: str = "chat_id_or_event_id_not_provided"
USER_ID_NOT_PROVIDED: str = "user_id_not_provided"
YOU_DONT_HAVE_PERMISSIONS_TO_DELETE_THIS_CHAT_ERROR: str = (
    "you_dont_have_permissions_to_delete_this_chat"
)
CHAT_DELETED_SUCCESS: str = "chat_deleted"
CHAT_NOT_FOUND_ERROR: str = "chat_not_found"


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    user_id: Optional[int] = data.get("user_id")
    chat_id: Optional[int] = data.get("chat_id")
    event_id: Optional[int] = data.get("event_id")

    if not event_id and not chat_id:
        raise ValueError(CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR)
    if not user_id:
        raise ValueError(USER_ID_NOT_PROVIDED)

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if chat_instance.is_group():
        if not check_user_is_chat_admin(chat=chat_instance, user_id=user_id):
            raise ValueError(YOU_DONT_HAVE_PERMISSIONS_TO_DELETE_THIS_CHAT_ERROR)
    else:
        if not check_user_is_chat_member(chat=chat_instance, user_id=user_id):
            raise ValueError(CHAT_NOT_FOUND_ERROR)


def set_chat_deleted_by_certain_user(user: dict[str, Any]) -> None:
    user["chat_deleted"] = True
    chat_instance.save()


def delete_chat(*, user_id: int, chat: Chat) -> None:
    user = find_user_in_chat_by_id(users=chat.users, user_id=user_id)
    if chat.type == Chat.Type.PERSONAL:
        set_chat_deleted_by_certain_user(user)

        if check_is_all_users_deleted_personal_chat(chat=chat):
            chat.delete()
    else:
        if user["author"]:
            chat.delete()
        else:
            remove_user_from_chat(user_id=user["user_id"], chat=chat)
    return CHAT_DELETED_SUCCESS


def delete_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = delete_chat(
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
        except ValueError as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id,
                ),
            )
