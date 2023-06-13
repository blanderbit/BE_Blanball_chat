from typing import Any, Optional

from django.conf import settings
from kafka import KafkaConsumer

from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.errors import (
    PROVIDED_INVALID_DATA_ERROR,
)
from chat.exceptions import (
    NotProvidedException
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_user_is_chat_admin,
    generate_response,
    get_chat,
    remove_unnecessary_data,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "edit_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "edit_chat_response"
CANT_EDIT_DISABLED_CHAT_ERROR: str = "chat_edit_disabled_chat"
YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_CHAT_ERROR: str = (
    "you_dont_have_permissions_to_edit_this_chat"
)

KEYS_IN_NEW_DATA_TO_KEEP: list[str] = ["name", "image"]

MESSAGE_TYPE: str = "edit_chat"


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    chat_id: Optional[int] = data.get("chat_id")
    event_id: Optional[int] = data.get("event_id")
    user_id: Optional[int] = data.get("user_id")

    if not event_id and not chat_id:
        raise NotProvidedException(fields=["event_id", "chat_id"])

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if chat_instance.disabled:
        raise ValueError(CANT_EDIT_DISABLED_CHAT_ERROR)
    if not user_id and chat_instance.is_group():
        raise NotProvidedException(fields=["user_id"])
    elif user_id and chat_instance.is_group():
        if not check_user_is_chat_admin(chat=chat_instance, user_id=user_id):
            raise ValueError(YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_CHAT_ERROR)


def edit_chat(*, chat: Chat, new_data: chat_data) -> Optional[str]:

    try:
        prepared_data = remove_unnecessary_data(
            new_data, *KEYS_IN_NEW_DATA_TO_KEEP
        )
        chat.__dict__.update(prepared_data)
        chat.save()

        return {
            "chat_id": chat.id,
            "users": chat.users,
            "new_data": remove_unnecessary_data(chat.__dict__)
        }
    except Exception:
        raise ValueError(PROVIDED_INVALID_DATA_ERROR)


def edit_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG
    )

    for data in consumer:
        request_id = data.value.get("request_id")
        try:
            validate_input_data(data.value)
            response_data = edit_chat(
                chat=chat_instance, new_data=data.value.get("new_data")
            )
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                ),
            )
        except ValueError as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                ),
            )
