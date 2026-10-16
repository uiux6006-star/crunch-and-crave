"""Create (or update) the admin user from environment variables.

Used on hosts like Render where the database is rebuilt on every deploy:

    DJANGO_ADMIN_USERNAME=admin DJANGO_ADMIN_PASSWORD=... python manage.py ensure_admin
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the admin user from DJANGO_ADMIN_USERNAME / DJANGO_ADMIN_PASSWORD."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "").strip()
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")

        if not username or not password:
            self.stdout.write("DJANGO_ADMIN_USERNAME / DJANGO_ADMIN_PASSWORD not set — skipping admin user.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f"Admin user '{username}' {'created' if created else 'updated'}."
        ))
