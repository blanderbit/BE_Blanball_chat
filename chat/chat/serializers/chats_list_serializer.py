from typing import Union

from rest_framework.serializers import (
    ModelSerializer,
)

from chat.models import Chat


class ChatsListSerializer(ModelSerializer):
    class Meta:
        model: Chat = Chat
        fields: Union[str, list[str]] = [
            "id",
            "name",
            "type",
            "image",
            "disabled",
            "last_message",
        ]
