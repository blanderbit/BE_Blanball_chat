from typing import Optional


class InvalidDataException(Exception):
    def __init__(self, message: Optional[str] = None) -> None:
        if not message:
            message = "invalid_provided_data"
        self.message = message
        super().__init__(self.message)


ACTION_INVALID_ERROR: str = "action_invalid"


class InvalidActionException(InvalidDataException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(ACTION_INVALID_ERROR)
