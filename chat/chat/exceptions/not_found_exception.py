from typing import Optional


class NotFoundException(Exception):

    def __init__(self, message: Optional[str], object: Optional[str] = None) -> None:
        if not message:
            message = 'object_not_found'
        if object:
            message = f'{object}_not_found'
        self.message = message
        super().__init__(self.message)
