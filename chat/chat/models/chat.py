from datetime import datetime
from typing import Any, Optional, Union, final

from decouple import config
from django.core.validators import (
    MinValueValidator,
)
from django.db import models
from django.db.models import Max, Q
from django.db.models.query import QuerySet

from chat.models.message import Messsage


@final
class Chat(models.Model):
    class Type(models.TextChoices):
        PERSONAL: str = "Personal"
        GROUP: str = "Group"
        EVENT_GROUP: str = "Event_Group"

    name: str = models.CharField(max_length=355, db_index=True, null=True)
    time_created: datetime = models.DateTimeField(auto_now_add=True)
    disabled: bool = models.BooleanField(default=False)
    type: str = models.CharField(
        choices=Type.choices, max_length=15, blank=False, null=False
    )
    # TODO нужно подумать о связи с моделей юзера
    users: Optional[dict[str, Union[str, int]]] = models.JSONField(
        default=list, db_index=True
    )
    event_id: Optional[int] = models.BigIntegerField(
        validators=[MinValueValidator(1)], null=True
    )
    image: Optional[str] = models.CharField(max_length=10000, null=True)
    messages: list[Optional[Messsage]] = models.ManyToManyField(
        Messsage, related_name="chat", blank=True, db_index=True
    )

    @property
    def chat_admins(self):
        return [
            user
            for user in self.users
            if user.get("admin")
            and not user.get("removed")
            and not user.get("chat_deleted")
        ]

    @property
    def chat_users_count_limit(self) -> int:
        return config("CHAT_USERS_COUNT_LIMIT", default=100, cast=int)

    @property
    def users_in_the_chat(self) -> list[dict[Union[bool, int]]]:
        return [
            user
            for user in self.users
            if not user["removed"] and not user["chat_deleted"]
        ]

    @property
    def chat_admins_count_limit(self) -> int:
        return config("CHAT_ADMINS_COUNT_LIMIT", default=3, cast=int)

    @property
    def last_message(self) -> Optional[str]:
        # first because order_by is -id
        last_message = self.messages.first()

        if last_message:
            return last_message.get_all_data()

    @property
    def is_group(self) -> bool:
        return self.type in self.CHAT_GROUP_TYPES()

    def __repr__(self) -> str:
        return "<Chat %s>" % self.id

    def __str__(self) -> str:
        return self.name

    def unread_messages_count(self, user_id: int) -> int:
        read_by_user_ids = self.messages.filter(
            Q(sender_id=user_id),
            Q(read_by__user_id=user_id) | Q(read_by=None)
        ).values_list("id", flat=True)

        unread_messages = self.messages.exclude(
            Q(type__in=Messsage.SERVICE_MESSAGE_TYPES()) | Q(id__in=read_by_user_ids)
        )

        return unread_messages.count()

    def get_all_chats_unread_messages_count_for_user(self, user_id: int) -> int:
        chats: QuerySet[
            Chat
        ] = self.get_only_available_chats_for_user_without_sortering(user_id)
        unread_count: int = 0

        for chat in chats:
            unread_count += chat.unread_messages_count(user_id=user_id)

        return unread_count

    def get_all_data(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "time_created": str(self.time_created),
            "type": self.type,
            "users": self.users,
            "disabled": self.disabled,
            "image": self.image,
        }

    @staticmethod
    def get_all() -> QuerySet["Chat"]:
        """
        getting all records with optimized selection from the database
        """
        return Chat.objects.prefetch_related("messages")

    @staticmethod
    def CHAT_GROUP_TYPES() -> list[str]:
        return [Chat.Type.GROUP, Chat.Type.EVENT_GROUP]

    @staticmethod
    def create_user_data_before_add_to_chat(
        *,
        user_id: int,
        is_author: bool = False,
        is_disabled: bool = False,
        is_removed: bool = False,
        is_admin: bool = False,
        is_chat_deleted: bool = False,
        is_chat_request: bool = False,
        is_send_push_notifications: bool = True,
        last_visble_message_id: Optional[int] = None
    ) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "author": is_author,
            "disabled": is_disabled,
            "removed": is_removed,
            "admin": is_admin,
            "chat_deleted": is_chat_deleted,
            "chat_request": is_chat_request,
            "push_notifications": is_send_push_notifications,
            "last_visble_message_id": last_visble_message_id,
        }

    @staticmethod
    def get_only_available_chats_for_user_without_sortering(
        user_id: int,
    ) -> QuerySet["Chat"]:
        filter_query: dict[str, Union[int, bool]] = {
            "user_id": user_id,
            "chat_deleted": False,
        }
        return Chat.get_all().filter(users__contains=[filter_query])

    @staticmethod
    def get_only_available_chats_for_user(user_id: int) -> QuerySet["Chat"]:
        return (
            Chat.get_only_available_chats_for_user_without_sortering(user_id)
            .annotate(last_message_time=Max("messages__time_created"))
            .order_by("-last_message_time", "-time_created", "-id")
        )

    class Meta:
        # the name of the table in the database for this model
        db_table: str = "chat"
        verbose_name: str = "chat"
        verbose_name_plural: str = "chats"
        # sorting database records for this model by default
        ordering: list[str] = ["-id"]
