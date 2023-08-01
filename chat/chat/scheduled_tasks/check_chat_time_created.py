import pandas
from config.celery import celery
from django.utils import timezone

from chat.utils.round_date_and_time import (
    round_date_and_time,
)


@celery.task
def check_chat_time_created() -> None:
    rounded_current_datetime = round_date_and_time(timezone.now())
