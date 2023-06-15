from typing import Union
from chat.models import Chat

from rest_framework.serializers import (
    ModelSerializer
)


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
