from typing import Any, Optional

from chat.models import Chat


def check_user_is_chat_member_and_not_author(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id and not user.get("author") for user in chat.users
    )


def check_user_is_chat_author(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id and user.get("author") for user in chat.users
    )


def check_user_is_chat_admin(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id and (user.get("author") or user.get("admin")) for user in chat.users
    )


def check_is_all_users_deleted_personal_chat(*, chat: Chat) -> bool:
    return all(user.get("chat_deleted") for user in chat.users)


def check_user_is_chat_member(*, chat: Chat, user_id: int) -> bool:
    return any(user.get("user_id") == user_id for user in chat.users)


def check_is_chat_group(*, chat: Chat) -> bool:
    return chat.type == Chat.Type.GROUP or chat.type == Chat.Type.EVENT_GROUP


def check_is_chat_disabled(*, chat: Chat) -> bool:
    return chat.disabled
