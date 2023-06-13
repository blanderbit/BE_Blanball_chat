from typing import Optional


class NotProvidedException(Exception):

    def __init__(self, message: Optional[str], fields: list[Optional[str]] = []) -> None:
        if not message:
            message = 'object_not_found'
        if len(fields) > 0 and not message:
            if len(fields) >= 2:
                message = f'{fields.join("_and_")}_not_provided'
            else:
                message = f'{fields[0]}_not_provided'
        self.message = message
        super().__init__(self.message)
