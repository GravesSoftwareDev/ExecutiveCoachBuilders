web: cd ecb_website && python manage.py migrate --noinput && python manage.py seed_vehicles && gunicorn ecb_website.wsgi --bind 0.0.0.0:$PORT --workers 2
