from chat.exceptions.not_provided_exception import (
    NotProvidedException as NotProvidedException
)
from chat.exceptions.not_found_exception import (
    NotFoundException as NotFoundException
)
from chat.exceptions.permissons_denied_exception import (
    PermissionsDeniedException as PermissionsDeniedException
)
from chat.exceptions.invalid_data_exception import (
    InvalidDataException as InvalidDataException
)

COMPARED_CHAT_EXCEPTIONS = (
    NotProvidedException,
    NotFoundException,
    PermissionsDeniedException,
    InvalidDataException,
)