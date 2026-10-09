"""
Django management command to verify customer unique constraints.
Usage: python manage.py verify_constraints
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Verify customer unique constraints are in place'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("CUSTOMER CONSTRAINT VERIFICATION")
        self.stdout.write("=" * 80)
        self.stdout.write("")

        with connection.cursor() as cursor:
            # Check for virtual columns
            cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'core_customer'
                AND COLUMN_NAME IN ('phone_normalized', 'email_normalized')
                ORDER BY COLUMN_NAME
            """)
            columns = cursor.fetchall()

            self.stdout.write("VIRTUAL COLUMNS:")
            self.stdout.write("-" * 80)
            if columns:
                for col in columns:
                    self.stdout.write(f"  {col[0]}:")
                    self.stdout.write(f"    Type: {col[1]}")
                    self.stdout.write(f"    Nullable: {col[2]}")
                    self.stdout.write(f"    Extra: {col[3]}")
                    self.stdout.write("")
            else:
                self.stdout.write(self.style.WARNING("  No virtual columns found"))
            self.stdout.write("")

            # Check for unique indexes
            cursor.execute("""
                SELECT INDEX_NAME, COLUMN_NAME, NON_UNIQUE
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'core_customer'
                AND INDEX_NAME IN ('customer_restaurant_phone_unique', 'customer_restaurant_email_unique')
                ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """)
            indexes = cursor.fetchall()

            self.stdout.write("UNIQUE INDEXES:")
            self.stdout.write("-" * 80)
            if indexes:
                for idx in indexes:
                    unique_str = "UNIQUE" if idx[2] == 0 else "NON-UNIQUE"
                    self.stdout.write(f"  {idx[0]}:")
                    self.stdout.write(f"    Column: {idx[1]}")
                    self.stdout.write(f"    Type: {unique_str}")
                    self.stdout.write("")
            else:
                self.stdout.write(self.style.WARNING("  No unique indexes found"))
            self.stdout.write("")

            # Test constraint behavior with sample data
            self.stdout.write("CONSTRAINT BEHAVIOR TEST:")
            self.stdout.write("-" * 80)

            # Test phone_normalized generation
            cursor.execute("""
                SELECT id, phone, phone_normalized
                FROM core_customer
                LIMIT 5
            """)
            phone_test = cursor.fetchall()
            self.stdout.write("Phone normalization sample:")
            for row in phone_test:
                self.stdout.write(f"  ID {row[0]}: phone='{row[1]}' -> phone_normalized='{row[2]}'")
            self.stdout.write("")

            # Test email_normalized generation
            cursor.execute("""
                SELECT id, email, email_normalized
                FROM core_customer
                LIMIT 5
            """)
            email_test = cursor.fetchall()
            self.stdout.write("Email normalization sample:")
            for row in email_test:
                self.stdout.write(f"  ID {row[0]}: email='{row[1]}' -> email_normalized='{row[2]}'")
            self.stdout.write("")

        self.stdout.write("=" * 80)
        self.stdout.write("VERIFICATION COMPLETE")
        self.stdout.write("=" * 80)
