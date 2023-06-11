from typing import Any


def remove_unnecessary_data(
    dictionary: dict[str, Any], *keys_to_keep: list[str]
) -> dict[str, Any]:
    return {
        key: dictionary.pop(key)
        for key in list(dictionary.keys())
        if key in keys_to_keep
    }
