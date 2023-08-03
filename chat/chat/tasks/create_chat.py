from typing import Any, Optional

from chat.decorators.set_required_fields import (
    set_required_fields,
)
from chat.exceptions import (
    InvalidDataException,
    NotProvidedException,
)
from chat.models import Chat, Messsage
from chat.serializers import (
    ServiceMessageSeralizer,
)
from chat.utils import (
    remove_duplicates_from_array,
    round_date_and_time,
)

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "create_chat"

chat_data = dict[str, Any]


@set_required_fields(["name", "request_user_id"])
def validate_input_data(data: chat_data) -> None:
    pass


def set_chat_type(data: chat_data) -> str:
    type: Optional[str] = data.get("type")
    chat_users: list[Optional[int]] = data.get("users", [])
    event_id: Optional[int] = data.get("event_id")

    if not type:
        if (
            len(chat_users) == 0
            or len(chat_users) >= 2
            and not data.get("user_id_for_request_chat")
        ):
            type = Chat.Type.GROUP if not event_id else Chat.Type.EVENT_GROUP
        else:
            type = Chat.Type.PERSONAL
    elif type == Chat.Type.EVENT_GROUP and not event_id:
        raise NotProvidedException(fields=["event_id"])

    return type


def create_chat(data: chat_data, return_instance: bool = False) -> Optional[chat_data]:
    users: list[Optional[int]] = data.get("users", [])
    event_id: Optional[int] = data.get("event_id")
    users.append(data["request_user_id"])
    users = remove_duplicates_from_array(users)

    chat_type: str = set_chat_type(data)
    chat_name: Optional[str] = data.get("name")

    try:
        chat: Chat = Chat.objects.create(
            name=chat_name,
            type=chat_type,
            event_id=event_id,
            users=[
                Chat.create_user_data_before_add_to_chat(
                    is_author=user == data["request_user_id"]
                    and chat_type != Chat.Type.PERSONAL,
                    is_chat_request=user == data.get("user_id_for_request_chat"),
                    user_id=user,
                )
                for user in users
            ],
        )

        chat.time_created = round_date_and_time(chat.time_created)
        chat.save()

        from chat.tasks.create_message import (
            create_service_message,
        )

        new_service_message = create_service_message(
            message_data={
                "type": Messsage.Type.GROUP_CHAT_CREATED,
            },
            chat=chat,
        )

        response_data: dict[str, Any] = {
            "users": chat.users,
            "service_message": ServiceMessageSeralizer(new_service_message).data,
            "chat_data": {
                "id": chat.id,
                "name": chat.name,
                "type": chat.type,
                "image": chat.image,
            },
        }

        if return_instance:
            response_data = {
                "chat": chat,
                "chat_data": response_data["chat_data"],
            }

        return response_data

    except Exception as _err:
        print(_err)
        raise InvalidDataException
