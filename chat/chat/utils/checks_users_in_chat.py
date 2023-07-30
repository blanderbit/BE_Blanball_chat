from chat.models import Chat


def is_valid_user(user: dict) -> bool:
    return is_user_in_chat(user) and not user.get("removed")


def is_user_in_chat(user: dict) -> bool:
    return not user.get("chat_deleted")


def check_user_is_chat_member_and_not_author(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id
        and is_valid_user(user)
        and not user.get("author")
        for user in chat.users
    )


def check_user_is_chat_author(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id and is_valid_user(user) and user.get("author")
        for user in chat.users
    )


def check_user_is_chat_admin(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id
        and is_valid_user(user)
        and (user.get("author") or user.get("admin"))
        for user in chat.users
    )


def check_is_all_users_deleted_personal_chat(*, chat: Chat) -> bool:
    return all(user.get("chat_deleted") for user in chat.users)


def check_user_in_chat(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id and is_user_in_chat(user) for user in chat.users
    )


def check_user_is_chat_member(*, chat: Chat, user_id: int) -> bool:
    return any(
        user.get("user_id") == user_id and is_valid_user(user=user)
        for user in chat.users
    )
