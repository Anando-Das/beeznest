# Generated for Phase 1B: Customer Duplicate Prevention
# MariaDB 10.4-compatible implementation using virtual generated columns

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_order_customer'),
    ]

    operations = [
        # Add virtual column for phone uniqueness
        # Returns NULL when phone is NULL or empty string, otherwise returns the phone value
        migrations.RunSQL(
            sql="""
                ALTER TABLE core_customer
                ADD COLUMN phone_normalized VARCHAR(20)
                GENERATED ALWAYS AS (NULLIF(TRIM(phone), '')) VIRTUAL
            """,
            reverse_sql="""
                ALTER TABLE core_customer DROP COLUMN phone_normalized
            """
        ),
        # Add unique index on (restaurant_id, phone_normalized)
        # Since phone_normalized is NULL for empty/NULL phones, this only enforces uniqueness on non-empty phones
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX customer_restaurant_phone_unique
                ON core_customer (restaurant_id, phone_normalized)
            """,
            reverse_sql="""
                DROP INDEX customer_restaurant_phone_unique ON core_customer
            """
        ),
        # Add virtual column for email uniqueness (case-insensitive)
        # Returns NULL when email is NULL or empty string, otherwise returns LOWER(email)
        migrations.RunSQL(
            sql="""
                ALTER TABLE core_customer
                ADD COLUMN email_normalized VARCHAR(254)
                GENERATED ALWAYS AS (NULLIF(TRIM(LOWER(email)), '')) VIRTUAL
            """,
            reverse_sql="""
                ALTER TABLE core_customer DROP COLUMN email_normalized
            """
        ),
        # Add unique index on (restaurant_id, email_normalized)
        # Since email_normalized is NULL for empty/NULL emails, this only enforces uniqueness on non-empty emails
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX customer_restaurant_email_unique
                ON core_customer (restaurant_id, email_normalized)
            """,
            reverse_sql="""
                DROP INDEX customer_restaurant_email_unique ON core_customer
            """
        ),
    ]
