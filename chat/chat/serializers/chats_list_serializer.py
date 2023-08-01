from typing import Optional, Union

from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
)

from chat.models import Chat


class ChatsListSerializer(ModelSerializer):
    unread_messages_count = SerializerMethodField()

    class Meta:
        model: Chat = Chat
        fields: Union[str, list[str]] = [
            "id",
            "name",
            "type",
            "image",
            "disabled",
            "last_message",
            "is_group",
            "unread_messages_count",
        ]

    def get_unread_messages_count(self, instance) -> Optional[int]:
        request_user_id: int = self.context["request_user_id"]
        return instance.unread_messages_count(request_user_id)
