from typing import Any, Optional, Union

data_type = Union[str, dict[str, Any], list[int]]


def prepare_response(*,
                     data: data_type,
                     keys_to_keep: list[Optional[str]] = []
                     ) -> data_type:
    return data
