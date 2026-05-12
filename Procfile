web: cd ecb_website && python manage.py migrate --noinput && gunicorn ecb_website.wsgi --bind 0.0.0.0:$PORT --workers 2
