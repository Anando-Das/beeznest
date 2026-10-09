"""
Django management command to audit customer duplicates.
Usage: python manage.py audit_customer_duplicates
"""

from django.core.management.base import BaseCommand
from core.models import Customer, Restaurant


class Command(BaseCommand):
    help = 'Audit customer table for duplicate phone numbers and email addresses per restaurant'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("CUSTOMER DUPLICATE AUDIT REPORT")
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # Get all customers
        all_customers = Customer.objects.all()
        total_customers = all_customers.count()
        self.stdout.write(f"Total customers in database: {total_customers}")
        self.stdout.write("")

        # Analyze data storage patterns
        self.stdout.write("DATA STORAGE PATTERNS")
        self.stdout.write("-" * 80)
        null_phones = all_customers.filter(phone__isnull=True).count()
        blank_phones = all_customers.filter(phone='').count()
        whitespace_phones = all_customers.exclude(phone__isnull=True).exclude(phone='').filter(phone__regex=r'^\s+$').count()
        non_null_phones = total_customers - null_phones

        null_emails = all_customers.filter(email__isnull=True).count()
        blank_emails = all_customers.filter(email='').count()
        whitespace_emails = all_customers.exclude(email__isnull=True).exclude(email='').filter(email__regex=r'^\s+$').count()
        non_null_emails = total_customers - null_emails

        self.stdout.write(f"Phone storage:")
        self.stdout.write(f"  NULL values: {null_phones}")
        self.stdout.write(f"  Empty strings (''): {blank_phones}")
        self.stdout.write(f"  Whitespace-only strings: {whitespace_phones}")
        self.stdout.write(f"  Non-NULL values: {non_null_phones}")
        self.stdout.write("")
        self.stdout.write(f"Email storage:")
        self.stdout.write(f"  NULL values: {null_emails}")
        self.stdout.write(f"  Empty strings (''): {blank_emails}")
        self.stdout.write(f"  Whitespace-only strings: {whitespace_emails}")
        self.stdout.write(f"  Non-NULL values: {non_null_emails}")
        self.stdout.write("")

        # Check for duplicate phone numbers per restaurant
        self.stdout.write("DUPLICATE PHONE NUMBERS (by restaurant)")
        self.stdout.write("-" * 80)
        phone_duplicates = []
        restaurants = Restaurant.objects.all()

        for restaurant in restaurants:
            # Get customers with non-empty, non-whitespace phones
            customers_with_phone = Customer.objects.filter(
                restaurant=restaurant
            ).exclude(phone__isnull=True).exclude(phone='').exclude(phone__regex=r'^\s+$')

            # Normalize phone numbers (strip whitespace)
            phone_to_customers = {}
            for customer in customers_with_phone:
                normalized_phone = customer.phone.strip()
                if normalized_phone not in phone_to_customers:
                    phone_to_customers[normalized_phone] = []
                phone_to_customers[normalized_phone].append(customer)

            # Find duplicates
            for phone, customers in phone_to_customers.items():
                if len(customers) > 1:
                    phone_duplicates.append({
                        'restaurant_id': restaurant.id,
                        'restaurant_name': restaurant.name,
                        'phone_masked': f"{phone[:3]}***{phone[-2:]}" if len(phone) >= 5 else "***",
                        'count': len(customers),
                        'customer_ids': [c.id for c in customers]
                    })

        if phone_duplicates:
            self.stdout.write(f"Found {len(phone_duplicates)} duplicate phone groups:")
            for dup in phone_duplicates:
                self.stdout.write(f"  Restaurant: {dup['restaurant_name']} (ID: {dup['restaurant_id']})")
                self.stdout.write(f"    Phone (masked): {dup['phone_masked']}")
                self.stdout.write(f"    Duplicate count: {dup['count']}")
                self.stdout.write(f"    Customer IDs: {dup['customer_ids']}")
                self.stdout.write("")
        else:
            self.stdout.write("No duplicate phone numbers found.")
        self.stdout.write("")

        # Check for duplicate email addresses per restaurant (case-insensitive)
        self.stdout.write("DUPLICATE EMAIL ADDRESSES (by restaurant, case-insensitive)")
        self.stdout.write("-" * 80)
        email_duplicates = []

        for restaurant in restaurants:
            # Get customers with non-empty, non-whitespace emails
            customers_with_email = Customer.objects.filter(
                restaurant=restaurant
            ).exclude(email__isnull=True).exclude(email='').exclude(email__regex=r'^\s+$')

            # Normalize email addresses (strip whitespace, lowercase)
            email_to_customers = {}
            for customer in customers_with_email:
                normalized_email = customer.email.strip().lower()
                if normalized_email not in email_to_customers:
                    email_to_customers[normalized_email] = []
                email_to_customers[normalized_email].append(customer)

            # Find duplicates
            for email, customers in email_to_customers.items():
                if len(customers) > 1:
                    # Mask email for reporting
                    parts = email.split('@')
                    if len(parts) == 2:
                        local, domain = parts
                        masked_local = local[:2] + "***" if len(local) > 2 else "***"
                        masked_email = f"{masked_local}@{domain}"
                    else:
                        masked_email = "***@***"
                    email_duplicates.append({
                        'restaurant_id': restaurant.id,
                        'restaurant_name': restaurant.name,
                        'email_masked': masked_email,
                        'count': len(customers),
                        'customer_ids': [c.id for c in customers]
                    })

        if email_duplicates:
            self.stdout.write(f"Found {len(email_duplicates)} duplicate email groups:")
            for dup in email_duplicates:
                self.stdout.write(f"  Restaurant: {dup['restaurant_name']} (ID: {dup['restaurant_id']})")
                self.stdout.write(f"    Email (masked): {dup['email_masked']}")
                self.stdout.write(f"    Duplicate count: {dup['count']}")
                self.stdout.write(f"    Customer IDs: {dup['customer_ids']}")
                self.stdout.write("")
        else:
            self.stdout.write("No duplicate email addresses found.")
        self.stdout.write("")

        # Summary
        self.stdout.write("=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Total customers: {total_customers}")
        self.stdout.write(f"Total restaurants: {restaurants.count()}")
        self.stdout.write(f"Duplicate phone groups: {len(phone_duplicates)}")
        self.stdout.write(f"Duplicate email groups: {len(email_duplicates)}")
        self.stdout.write("")

        # Constraint implications
        self.stdout.write("CONSTRAINT IMPLICATIONS")
        self.stdout.write("-" * 80)
        if phone_duplicates or email_duplicates:
            self.stdout.write(self.style.WARNING("WARNING: Existing duplicates found."))
            self.stdout.write("Adding conditional unique constraints (restaurant, phone) and (restaurant, email)")
            self.stdout.write("would fail due to existing duplicate records.")
            self.stdout.write("")
            self.stdout.write("The constraints would need to be:")
            self.stdout.write("  - Partial unique index on (restaurant_id, phone) WHERE phone IS NOT NULL AND phone != ''")
            self.stdout.write("  - Partial unique index on (restaurant_id, email) WHERE email IS NOT NULL AND email != ''")
            self.stdout.write("")
            self.stdout.write("Current duplicate handling in order creation:")
            self.stdout.write("  - Phone: Uses .first() to get existing customer, updates name/email if provided")
            self.stdout.write("  - Email: No deduplication logic on email alone")
            self.stdout.write("  - This can lead to multiple customers with same email but different phones")
        else:
            self.stdout.write(self.style.SUCCESS("No duplicates found. Conditional unique constraints can be safely added."))
        self.stdout.write("")

        self.stdout.write("=" * 80)
        self.stdout.write("AUDIT COMPLETE")
        self.stdout.write("=" * 80)
