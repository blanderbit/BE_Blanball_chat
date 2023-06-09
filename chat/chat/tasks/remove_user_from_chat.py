from typing import Any

from kafka import KafkaConsumer, KafkaProducer
from django.conf import settings
from chat.models import Chat
from chat.tasks.utils import (
    RESPONSE_STATUSES,
    generate_response,
)
from chat.tasks.default_producer import (
    default_producer
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = 'remove_user_from_chat'

# the name of the topic to which we send the answer
RESPONSE_TOPIC_NAME: str = 'remove_user_from_chat_response'

MESSAGE_TYPE: str = 'remove_user_from_chat'

USER_ID_NOT_PROVIDED_ERROR: str = 'user_id_not_provided'
CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR: str = 'chat_id_or_event_id_not_provided'
CHAT_NOT_FOUND_ERROR: str = 'chat_not_found'
CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT: str = 'cant_remove_user_who_not_in_the_chat'
USER_REMOVED_FROM_THE_CHAT_SUCCESS: str = 'user_removed_from_the_chat'
YOU_DONT_HAVE_PERMISSIONS_TO_REMOVE_USER_FROM_THIS_CHAT_ERROR: str = 'you_dont_have_permissions_to_remove_user_from_this_chat'
CANT_REMOVE_USER_FROM_PERSONAL_CHAT: str = 'cant_remove_user_from_personal_chat'


chat_data = dict[str, Any]


def validate_input_data(data: chat_data) -> None:
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    event_id = data.get("event_id")
    sender_user_id = data.get("sender_user_id")

    if not user_id:
        raise ValueError(USER_ID_NOT_PROVIDED_ERROR)
    if not event_id and not chat_id:
        raise ValueError(CHAT_ID_OR_EVENT_ID_NOT_PROVIDED_ERROR)

    try:
        global chat_instance

        if chat_id:
            chat_instance = Chat.objects.get(id=chat_id)
        else:
            chat_instance = Chat.objects.filter(event_id=event_id)[0]

            if not chat_instance:
                raise ValueError(CHAT_NOT_FOUND_ERROR)

        if sender_user_id:

            if chat_instance.type == Chat.Type.PERSONAL:
                raise ValueError(CANT_REMOVE_USER_FROM_PERSONAL_CHAT)

            if not any(user.get("user_id") == sender_user_id and user.get("author") == True for user in chat_instance.users):
                raise ValueError(
                    YOU_DONT_HAVE_PERMISSIONS_TO_REMOVE_USER_FROM_THIS_CHAT_ERROR
                )

        if not any(user.get("user_id") == user_id for user in chat_instance.users):
            raise ValueError(CANT_REMOVE_USER_WHO_NOT_IN_THE_CHAT)

    except Chat.DoesNotExist:
        raise ValueError(CHAT_NOT_FOUND_ERROR)


def remove_user_from_chat(user_id: int) -> str:
    filtered_users = filter(
        lambda user: user['user_id'] == user_id, chat_instance.users)
    user_to_remove = next(filtered_users, None)

    if user_to_remove:
        chat_instance.users.remove(user_to_remove)
    if len(chat_instance.users) == 0:
        chat_instance.delete()

    return USER_REMOVED_FROM_THE_CHAT_SUCCESS


def remove_user_from_chat_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(
        TOPIC_NAME, **settings.KAFKA_CONSUMER_CONFIG)

    for data in consumer:

        request_id = data.value.get("request_id")

        try:
            validate_input_data(data.value)
            response_data = remove_user_from_chat(data.value.get("user_id"))
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["SUCCESS"],
                    data=response_data,
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                )
            )
        except ValueError as err:
            default_producer(
                RESPONSE_TOPIC_NAME,
                generate_response(
                    status=RESPONSE_STATUSES["ERROR"],
                    data=str(err),
                    message_type=MESSAGE_TYPE,
                    request_id=request_id
                )
            )
