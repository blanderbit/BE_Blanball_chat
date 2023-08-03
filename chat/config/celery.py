import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

celery = Celery("config")

celery.config_from_object("django.conf:settings", namespace="CELERY")
celery.autodiscover_tasks()
