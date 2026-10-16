#!/usr/bin/env bash
# Render start step. The free plan's disk is reset on every deploy/restart,
# so the database (menu, promo codes, admin user) is rebuilt here each time.
set -o errexit

python manage.py migrate --noinput
python manage.py ensure_admin
exec gunicorn njfastfood.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers "${WEB_CONCURRENCY:-2}" --timeout 60
