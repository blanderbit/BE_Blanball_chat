from datetime import datetime, timedelta
from typing import Any, Optional, Union, final

from decouple import config
from django.core.validators import (
    MinValueValidator,
)
from django.db import models
from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils import timezone


@final
class Messsage(models.Model):
    sender_id: int = models.BigIntegerField(validators=[MinValueValidator(1)])
    text: str = models.CharField(max_length=500, db_index=True)
    time_created: datetime = models.DateTimeField(auto_now_add=True)
    readed_by: bool = models.JSONField(default=list, db_index=True)
    disabled: bool = models.BooleanField(default=False)
    edited: bool = models.BooleanField(default=False)
    reply_to: int = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="replies"
    )

    def __repr__(self) -> str:
        return "<Messsage %s>" % self.id

    def __str__(self) -> str:
        return self.text

    def is_expired_to_edit(self) -> bool:
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        return self.time_created <= ten_minutes_ago

    def mark_as_read(self, user_id: int) -> None:
        if user_id != self.sender_id:
            existing_users = [user["user_id"] for user in self.readed_by]
            if user_id not in existing_users:
                self.readed_by.append(
                    {"user_id": user_id, "time_when_was_readed": str(timezone.now())}
                )
                self.save()

    def mark_as_unread(self, user_id: int) -> None:
        if user_id != self.sender_id:
            self.readed_by = [
                message for message in self.readed_by if message["user_id"] != user_id
            ]
            self.save()

    def get_all_data(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "text": self.text,
            "time_created": str(self.time_created),
        }

    @staticmethod
    def get_all() -> QuerySet["Chat"]:
        """
        getting all records with optimized selection from the database
        """
        return Messsage.objects.all()

    class Meta:
        # the name of the table in the database for this model
        db_table: str = "message"
        verbose_name: str = "message"
        verbose_name_plural: str = "messages"
        # sorting database records for this model by default
        ordering: list[str] = ["-id"]


@final
class Chat(models.Model):
    class Type(models.TextChoices):
        PERSONAL: str = "Personal"
        GROUP: str = "Group"
        EVENT_GROUP: str = "Event_Group"

    name: str = models.CharField(max_length=355, db_index=True)
    time_created: datetime = models.DateTimeField(auto_now_add=True)
    disabled: bool = models.BooleanField(default=False)
    type: str = models.CharField(
        choices=Type.choices, max_length=15, blank=False, null=False
    )
    # TODO нужно подумать о связи с моделей юзера
    users: Optional[dict[str, Union[str, int]]] = models.JSONField(default=list, db_index=True)
    event_id: Optional[int] = models.BigIntegerField(
        validators=[MinValueValidator(1)], null=True
    )
    image: Optional[str] = models.CharField(max_length=10000, null=True)
    messages: list[Optional[Messsage]] = models.ManyToManyField(
        Messsage, related_name="chat", blank=True,
        db_index=True
    )
    chat_request_user_id: int = models.BigIntegerField(
        validators=[MinValueValidator(1)], null=True
    )

    @property
    def chat_admins(self):
        return [user for user in self.users if user.get("admin")]

    @property
    def chat_users_count_limit(self) -> int:
        return config("CHAT_USERS_COUNT_LIMIT", default=100, cast=int)

    @property
    def chat_admins_count_limit(self) -> int:
        return config("CHAT_ADMINS_COUNT_LIMIT", default=3, cast=int)

    @property
    def last_message(self) -> Optional[str]:
        message = Messsage.objects.filter(chat__id=self.id).last()

        if message:
            return message.text

    def __repr__(self) -> str:
        return "<Chat %s>" % self.id

    def __str__(self) -> str:
        return self.name

    def is_group(self) -> bool:
        return self.type == Chat.Type.GROUP or self.type == Chat.Type.EVENT_GROUP

    def unread_messages_count(self, user_id: int) -> int:
        filter_query: dict[str, int] = {
            "user_id": user_id,
        }
        return self.messages.exclude(readed_by__contains=[filter_query]).count()

    def get_all_chats_unread_messages_count_for_user(self, user_id: int) -> int:
        chats: QuerySet[Chat] = self.get_only_available_chats_for_user(user_id)
        unread_count: int = 0

        for chat in chats:
            unread_count += chat.unread_messages_count(user_id=user_id)

        return unread_count

    @staticmethod
    def get_all() -> QuerySet["Chat"]:
        """
        getting all records with optimized selection from the database
        """
        return Chat.objects.prefetch_related("messages")

    def get_all_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "time_created": str(self.time_created),
            "type": self.type,
            "users": self.users,
            "disabled": self.disabled,
            "image": self.image,
        }

    @staticmethod
    def create_user_data_before_add_to_chat(
        *,
        is_author: bool,
        is_disabled: bool = False,
        is_removed: bool = False,
        is_admin: bool = False,
        is_chat_deleted: bool = False,
        user_id: int,
    ) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "author": is_author,
            "disabled": is_disabled,
            "removed": is_removed,
            "admin": is_admin,
            "chat_deleted": is_chat_deleted,
        }

    @staticmethod
    def get_only_available_chats_for_user_without_sortering(user_id: int) -> QuerySet["Chat"]:
        filter_query: dict[str, Union[int, bool]] = {
            "user_id": user_id,
            "chat_deleted": False,
        }
        return Chat.get_all().filter(users__contains=[filter_query])

    @staticmethod
    def get_only_available_chats_for_user(user_id: int) -> QuerySet["Chat"]:
        return (
            Chat.get_only_available_chats_for_user_without_sortering(user_id)
            .annotate(message_count=Count("messages"))
            .order_by(
                "-messages__time_created", "-time_created", "-message_count", "-id"
            )
        )

    class Meta:
        # the name of the table in the database for this model
        db_table: str = "chat"
        verbose_name: str = "chat"
        verbose_name_plural: str = "chats"
        # sorting database records for this model by default
        ordering: list[str] = ["-id"]
