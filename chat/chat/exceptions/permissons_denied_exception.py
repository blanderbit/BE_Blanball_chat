from typing import Optional


class PermissionsDeniedException(Exception):

    def __init__(self, message: Optional[str] = None) -> None:
        if not message:
            message = 'permissions_denied'
        self.message = message
        super().__init__(self.message)
