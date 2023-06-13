from typing import Optional
from django.core.paginator import Paginator, InvalidPage
from django.db.models.query import QuerySet


def custom_pagination(*,
                      queryset: QuerySet,
                      page: int = 1,
                      offset: int = 10,
                      fields: Optional[list[str]] = None
                      ) -> dict:
    paginator = Paginator(queryset, offset)

    try:
        page_objects = paginator.page(page)
        serialized_data = serialize_queryset(page_objects.object_list, fields)

        return {
            "current_page": page,
            "total_count": paginator.count,
            "results": serialized_data,
        }

    except InvalidPage:
        raise ValueError("invalid_page")


def custom_json_field_pagination(*,
                                 model_instance,
                                 field_name: str,
                                 page: int = 1,
                                 offset: int = 10
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
        raise ValueError("invalid_page")


def serialize_queryset(queryset, fields=None):
    serialized_data = []

    for obj in queryset:
        serialized_obj = serialize_object(obj, fields)
        serialized_data.append(serialized_obj)

    return serialized_data


def serialize_object(obj, fields=None):
    serialized_obj = {}

    if fields is None:
        # If fields are not specified, serialize all fields
        fields = [field.name for field in obj._meta.fields]

    for field in fields:
        serialized_obj[field] = getattr(obj, field)

    return serialized_obj
