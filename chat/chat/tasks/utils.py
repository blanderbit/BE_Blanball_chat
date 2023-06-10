from typing import Any, Optional

from chat.models import Chat

RESPONSE_STATUSES: dict[str, str] = {"ERROR": "error", "SUCCESS": "success"}
CHAT_NOT_FOUND_ERROR: str = "chat_not_found"


def check_is_all_users_deleted_personal_chat(*, chat: Chat) -> bool:
    return all(user.get("chat_deleted") for user in chat.users)


def check_user_is_chat_member(*, chat: Chat, user_id: int) -> bool:
    return any(user.get("user_id") == user_id for user in chat.users)


def check_user_is_chat_member_and_not_author(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id and not user.get("author") for user in chat.users
    )


def check_user_is_chat_author(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id and user.get("author") for user in chat.users
    )


def find_user_in_chat_by_id(
    *, users: list[int], user_id: int
) -> Optional[dict[str, Any]]:
    filtered_users = filter(lambda user: user["user_id"] == user_id, users)
    return next(filtered_users, None)


def get_chat(*, chat_id: Optional[int] = None, event_id: Optional[int] = None) -> Chat:

    try:
        if chat_id:
            chat_instance = Chat.objects.get(id=chat_id)
        else:
            chat_instance = Chat.objects.filter(event_id=event_id)[0]

            if not chat_instance:
                raise ValueError(CHAT_NOT_FOUND_ERROR)
    except Chat.DoesNotExist:
        raise ValueError(CHAT_NOT_FOUND_ERROR)

    return chat_instance


def generate_response(
    *, status: str, data: Any, message_type: str, request_id: Optional[str] = None
) -> dict[str, Any]:
    if request_id:
        return {
            "message_type": message_type,
            "request_id": request_id,
            "status": status,
            "data": data,
        }
    return {"message_type": message_type, "status": status, "data": data}
