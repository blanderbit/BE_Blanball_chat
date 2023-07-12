from typing import Any, Optional
from django.core.paginator import (
    InvalidPage,
    Paginator,
)
from django.db.models.query import QuerySet

from chat.exceptions import InvalidDataException


def custom_pagination(
    *,
    queryset: QuerySet,
    page: int = 1,
    offset: int = 10,
    serializer_class,
    serializer_context: Optional[dict[str, Any]] = None,
    helpfull_data: Optional[dict[str, Any]] = None
) -> dict:
    paginator = Paginator(queryset, offset)

    try:
        page_objects = paginator.page(page)
        serialized_data = serializer_class(
            page_objects.object_list,
            many=True,
            context=serializer_context
        ).data

        return {
            "current_page": page,
            "total_count": paginator.count,
            "results": serialized_data,
            "helpfull_data": helpfull_data,
            "is_next_page": page_objects.has_next(),
            "is_prev_page": page_objects.has_previous()
        }

    except InvalidPage:
        raise InvalidDataException(message="invalid_page")


def filter_list(items: list[dict[str, Any]], filter_params: dict[str, Any]) -> list[dict[str, Any]]:
    filtered_items = []
    key, value = next(iter(filter_params.items()))
    for item in items:
        if item.get(key) == value:
            filtered_items.append(item)
    return filtered_items


def custom_json_field_pagination(
    *, model_instance,
    field_name: str,
    page: int = 1,
    offset: int = 10,
    filter_params: Optional[dict[str, Any]] = None,
    helpfull_data: Optional[dict[str, Any]] = None
) -> dict:
    queryset = getattr(model_instance, field_name)

    if filter_params:
        if isinstance(queryset, list):
            queryset = filter_list(queryset, filter_params)
        else:
            queryset = queryset.filter(**filter_params)

    paginator = Paginator(queryset, offset)

    try:
        page_objects = paginator.page(page)

        return {
            "current_page": page,
            "total_count": paginator.count,
            "results": page_objects.object_list,
            "helpfull_data": helpfull_data,
            "is_next_page": page_objects.has_next(),
            "is_prev_page": page_objects.has_previous()
        }

    except InvalidPage:
        raise InvalidDataException(message="invalid_page")
