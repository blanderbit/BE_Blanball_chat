from datetime import datetime, timedelta
from typing import Any, final

from django.core.validators import (
    MinValueValidator,
)
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone


@final
class Messsage(models.Model):
    class Type(models.TextChoices):
        USER_MESSAGE: str = "user_message"
        USER_JOINED_TO_CHAT: str = "user_joined_to_chat"

    sender_id: int = models.BigIntegerField(validators=[MinValueValidator(1)])
    text: str = models.CharField(max_length=500, db_index=True)
    time_created: datetime = models.DateTimeField(auto_now_add=True)
    readed_by: bool = models.JSONField(default=list, db_index=True)
    disabled: bool = models.BooleanField(default=False)
    edited: bool = models.BooleanField(default=False)
    type: str = models.CharField(
        choices=Type.choices, max_length=255, default=Type.USER_MESSAGE
    )
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

    def is_system_chat_message(self) -> bool:
        return not self.type == self.Type.USER_MESSAGE

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
