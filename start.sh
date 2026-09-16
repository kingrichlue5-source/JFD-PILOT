#!/bin/bash
set -e

echo "Running collectstatic..."
python manage.py collectstatic --noinput

echo "Running migrate..."
python manage.py migrate --noinput

echo "Ensuring inventory user exists..."
python manage.py add_inventory_user || true

echo "Starting gunicorn..."
exec gunicorn jfd_hms.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120
