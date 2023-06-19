from typing import Any, Optional, Union


data_type = Union[str, dict[str, Any]]


def prepare_response(*,
                     data: data_type,
                     keys_to_keep: list[Optional[str]] = []
                     ) -> data_type:

    if isinstance(data, dict):
        send_data = {}
        if len(keys_to_keep == 0):
            send_data = data
        for key in list(data.keys()):
            if key not in keys_to_keep:
                send_data[key] = data.pop(key)
    data['send_data'] = send_data
    return data
