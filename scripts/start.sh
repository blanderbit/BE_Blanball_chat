cd chat
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py loaddata */fixtures/*.json
python manage.py runserver 0.0.0.0:12000 &
python manage.py start_consume_messages