#!/usr/bin/env bash
# Render build step: install libraries and prepare CSS/JS.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
