from typing import Union

from rest_framework.serializers import (
    ModelSerializer,
)

from chat.models import Messsage


class ServiceMessageSeralizer(ModelSerializer):
    class Meta:
        model: Messsage = Messsage
        fields: Union[str, list[str]] = [
            "id",
            "sender_id",
            "time_created",
            "service",
            "type",
        ]
