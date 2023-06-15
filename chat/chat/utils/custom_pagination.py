from chat.exceptions import (
    InvalidDataException
)
from django.core.paginator import (
    InvalidPage,
    Paginator,
)
from django.db.models.query import QuerySet


def custom_pagination(
    *,
    queryset: QuerySet,
    page: int = 1,
    offset: int = 10,
    serializer_class,
) -> dict:
    paginator = Paginator(queryset, offset)

    try:
        page_objects = paginator.page(page)
        serialized_data = serializer_class(page_objects.object_list, many=True).data

        return {
            "current_page": page,
            "total_count": paginator.count,
            "results": serialized_data,
        }

    except InvalidPage:
        raise InvalidDataException(message="invalid_page")


def custom_json_field_pagination(
    *, model_instance, field_name: str, page: int = 1, offset: int = 10
) -> dict:
    queryset = getattr(model_instance, field_name)
    paginator = Paginator(queryset, offset)

    try:
        page_objects = paginator.page(page)

        return {
            "current_page": page,
            "total_count": paginator.count,
            "results": page_objects.object_list,
        }

    except InvalidPage:
        raise InvalidDataException(message="invalid_page")
