from chat.exceptions import NotProvidedException


def set_required_fields(required_fields: list[str]):
    def decorator(func):
        def wrapper(data):
            for fields in required_fields:
                if isinstance(fields, str):
                    fields = [fields]
                has_at_least_one = False
                for field in fields:
                    if field in data and data[field] is not None:
                        has_at_least_one = True
                        break
                if not has_at_least_one:
                    raise NotProvidedException(fields=fields)
            return func(data)

        return wrapper

    return decorator
