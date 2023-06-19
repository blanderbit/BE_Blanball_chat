from typing import Any, Optional, Union


data_type = Union[str, dict[str, Any], list[int]]


def prepare_response(*,
                     data: data_type,
                     keys_to_keep: list[Optional[str]] = []
                     ) -> data_type:

    send_data = {}
    if isinstance(data, dict):
        if len(keys_to_keep) == 0:
            send_data = data
        for key in list(data.keys()):
            if key not in keys_to_keep:
                data[key] = data.pop(key)
    else:
        send_data = data
    send_data['main_data'] = data
    return send_data
