#!/bin/bash
cd chat

Api()
{
    python manage.py makemigrations --noinput
    python manage.py migrate --noinput
    python manage.py loaddata */fixtures/*.json
    python manage.py runserver 0.0.0.0:8000 &
    python manage.py start_consume_messages
}

CeleryWorker()
{
    celery -A config worker --loglevel=INFO --concurrency=8 -O fair -P prefork -n cel_app_worker
}


CeleryBeat()
{
    celery -A config beat -l info 
}


case $1
in
    api) Api ;;
    celery-worker) CeleryWorker ;;
    celery-beat) CeleryBeat ;;
    *) exit 1 ;;
esac