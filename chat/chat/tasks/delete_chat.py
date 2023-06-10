from typing import Any

from django.conf import settings
from kafka import KafkaConsumer, KafkaProducer

from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.tasks.remove_user_from_chat import (
    remove_user_from_chat,
)
from chat.tasks.utils import (
    RESPONSE_STATUSES,
    check_is_all_users_deleted_personal_chat,
    check_user_is_chat_author,
    check_user_is_chat_member,
    find_user_in_chat_by_id,
    generate_response,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "delete_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "delete_chat_response"

MESSAGE_TYPE: str = "delete_chat"


CHAT_ID_NOT_PROVIDED: str = "chat_id_not_provided"
USER_ID_NOT_PROVIDED: str = "user_id_not_provided"
CHAT_NOT_FOUND_ERROR: str = "chat_not_found"
YOU_DONT_HAVE_PERMISSIONS_TO_DELETE_THIS_CHAT_ERROR: str = (
    "you_dont_have_permissions_to_delete_this_chat"
)
CHAT_DELETED_SUCCESS: str = "chat_deleted"


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")

    if not chat_id:
        raise ValueError(CHAT_ID_NOT_PROVIDED)
    if not user_id:
        raise ValueError(USER_ID_NOT_PROVIDED)

    try:
        global chat_instance
        chat_instance = Chat.objects.get(id=chat_id)

        if (
            chat_instance.type == Chat.Type.GROUP
            or chat_instance.type == Chat.Type.EVENT_GROUP
        ):
            if not check_user_is_chat_author(chat=chat_instance, user_id=user_id):
                raise ValueError(YOU_DONT_HAVE_PERMISSIONS_TO_DELETE_THIS_CHAT_ERROR)
        else:
            if not check_user_is_chat_member(chat=chat_instance, user_id=user_id):
                raise ValueError(CHAT_NOT_FOUND_ERROR)

    except Chat.DoesNotExist:
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
