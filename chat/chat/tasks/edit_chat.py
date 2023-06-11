from typing import Any

from django.conf import settings
from kafka import KafkaConsumer

from chat.models import Chat
from chat.tasks.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    check_is_chat_group,
    check_user_is_chat_admin,
    generate_response,
    get_chat,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "edit_chat"

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = "edit_chat_response"
CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR: str = "chat_id_or_event_id_not_provided"
CHAT_EDITED_SUCCESS: str = "chat_edited"
USER_ID_NOT_PROVIDED: str = "user_id_not_provided"
YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_CHAT_ERROR: str = (
    "you_dont_have_permissions_to_edit_this_chat"
)
CHAT_EDITED_SUCCESS: str = "chat_edited_success"

KEYS_IN_NEW_DATA_TO_KEEP: list[str] = ["name", "image"]

MESSAGE_TYPE: str = "edit_chat"


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    chat_id = data.get("chat_id")
    event_id = data.get("event_id")
    user_id = data.get("user_id")

    if not event_id and not chat_id:
        raise ValueError(CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR)

    global chat_instance
    chat_instance = get_chat(chat_id=chat_id, event_id=event_id)

    if not user_id and check_is_chat_group(chat=chat_instance):
        raise ValueError(USER_ID_NOT_PROVIDED)
    elif user_id and check_is_chat_group(chat=chat_instance):
        if not check_user_is_chat_admin(chat=chat_instance, user_id=user_id):
            raise ValueError(YOU_DONT_HAVE_PERMISSIONS_TO_EDIT_THIS_CHAT_ERROR)


def prepare_new_data_before_edit_chat(
    dictionary: dict[str, Any], *keys_to_keep: list[str]
) -> dict[str, Any]:
    return {
        key: dictionary.pop(key)
        for key in list(dictionary.keys())
        if key in keys_to_keep
    }


def edit_chat(*, chat: Chat, new_data: chat_data) -> None:
    prepared_data = prepare_new_data_before_edit_chat(
        new_data, *KEYS_IN_NEW_DATA_TO_KEEP
    )
    chat.__dict__.update(prepared_data)
    chat.save()

    return CHAT_EDITED_SUCCESS


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
