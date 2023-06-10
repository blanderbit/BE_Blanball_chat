from datetime import datetime
from typing import Any, Optional, Union, final

from django.core.validators import (
    MinValueValidator,
)
from django.db import models
from django.db.models.query import QuerySet


@final
class Chat(models.Model):
    class Type(models.TextChoices):
        PERSONAL: str = "Personal"
        GROUP: str = "Group"
        EVENT_GROUP: str = "Event_Group"

    name: str = models.CharField(max_length=355)
    time_created: datetime = models.DateTimeField(auto_now_add=True)
    disabled: bool = models.BooleanField(default=False)
    type: str = models.CharField(
        choices=Type.choices, max_length=15, blank=False, null=False
    )
    users: Optional[dict[str, Union[str, int]]] = models.JSONField(null=True)
    event_id: Optional[int] = models.BigIntegerField(
        validators=[MinValueValidator(1)], null=True
    )
    image: Optional[str] = models.CharField(max_length=10000, null=True)

    def __repr__(self) -> str:
        return "<Chat %s>" % self.id

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def get_all() -> QuerySet["Chat"]:
        """
        getting all records with optimized selection from the database
        """
        return Chat.objects.all()

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

    class Meta:
        # the name of the table in the database for this model
        db_table: str = "chat"
        verbose_name: str = "chat"
        verbose_name_plural: str = "chats"


@final
class Messsage(models.Model):
    sender_id: int = models.BigIntegerField(validators=[MinValueValidator(1)])
    text: str = models.CharField(max_length=500)
    time_created: datetime = models.DateTimeField(auto_now_add=True)
    disabled: bool = models.BooleanField(default=False)
    readed_by: bool = models.JSONField(null=True)
    chat: Chat = models.ForeignKey(Chat, on_delete=models.CASCADE)

    def __repr__(self) -> str:
        return "<Messsage %s>" % self.id

    def __str__(self) -> str:
        return self.text

    @staticmethod
    def get_all() -> QuerySet["Chat"]:
        """
        getting all records with optimized selection from the database
        """
        return Messsage.objects.select_related("chat")

    class Meta:
        # the name of the table in the database for this model
        db_table: str = "message"
        verbose_name: str = "message"
        verbose_name_plural: str = "messages"
