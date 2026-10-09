"""
Django management command to check database version and engine.
Usage: python manage.py check_db_version
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Check database version and engine'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            self.stdout.write(f"Database version: {version}")

            cursor.execute("SHOW VARIABLES LIKE 'version_comment'")
            comment = cursor.fetchone()
            if comment:
                self.stdout.write(f"Database engine: {comment[1]}")

            cursor.execute("SHOW VARIABLES LIKE 'storage_engine'")
            storage = cursor.fetchone()
            if storage:
                self.stdout.write(f"Default storage engine: {storage[1]}")

            # Check for functional index support
            cursor.execute("SHOW VARIABLES LIKE 'version'")
            version_num = cursor.fetchone()[1]
            major_minor = tuple(map(int, version_num.split('.')[:2]))
            if major_minor >= (10, 4):
                self.stdout.write(self.style.SUCCESS("[OK] Functional indexes supported (MariaDB 10.4+)"))
            else:
                self.stdout.write(self.style.WARNING("[WARN] Functional indexes not supported"))

            # Check for generated column support
            if major_minor >= (10, 2):
                self.stdout.write(self.style.SUCCESS("[OK] Generated columns supported (MariaDB 10.2+)"))
            else:
                self.stdout.write(self.style.WARNING("[WARN] Generated columns not supported"))
