from typing import Any, Optional


def find_user_in_chat_by_id(
    *, users: list[int], user_id: int
) -> Optional[dict[str, Any]]:
    filtered_users = filter(lambda user: user["user_id"] == user_id, users)
    return next(filtered_users, None)
