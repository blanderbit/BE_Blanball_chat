from typing import Union
from chat.models import Messsage

from rest_framework.serializers import (
    ModelSerializer
)


class ReplyToSerilizer(ModelSerializer):
    class Meta:
        model: Messsage = Messsage
        fields: Union[str, list[str]] = [
            "id",
            "text",
        ]


class MessagesListSerializer(ModelSerializer):

    reply_to = ReplyToSerilizer()

    class Meta:
        model: Messsage = Messsage
        fields: Union[str, list[str]] = [
            "id",
            "sender_id",
            "text",
            "time_created",
            "edited",
            "readed_by",
            "reply_to"
        ]
