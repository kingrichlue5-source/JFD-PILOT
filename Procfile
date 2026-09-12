web: python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn jfd_hms.wsgi --bind 0.0.0.0:$PORT --workers 3 --timeout 120
