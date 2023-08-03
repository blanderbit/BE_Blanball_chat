from chat.decorators import set_required_fields
from chat.models import Chat

# the name of the main topic that we
# are listening to receive data from outside
TOPIC_NAME: str = "get_chats_count"


@set_required_fields(["request_user_id"])
def validate_input_data(data: dict[str, int]) -> None:
    pass


def get_chats_count(*, data: dict[str, int]) -> dict[str, int]:
    request_user_id = data["request_user_id"]

    all_chats_count: int = 0
    personal_chats_count: int = 0
    group_chats_count: int = 0
    chat_requests_count: int = 0

    all_users_chats = Chat.get_only_available_chats_for_user_without_sortering(
        request_user_id
    )

    if len(all_users_chats) > 0:
        all_chats_count = all_users_chats.count()
        personal_chats_count = all_users_chats.filter(type=Chat.Type.PERSONAL).count()
        group_chats_count = all_users_chats.filter(
            type__in=Chat.CHAT_GROUP_TYPES()
        ).count()
        chat_requests_count = all_users_chats.filter(
            users__contains=[
                {
                    "user_id": request_user_id,
                    "chat_request": True,
                }
            ]
        ).count()

    chats_count_info: dict[str, int] = {
        "all_chats_count": all_chats_count,
        "personal_chats_count": personal_chats_count,
        "group_chats_count": group_chats_count,
        "chat_requests_count": chat_requests_count,
    }

    return chats_count_info
