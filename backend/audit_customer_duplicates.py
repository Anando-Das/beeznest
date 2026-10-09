"""
Customer Duplicate Audit Script
Audits the Customer table for duplicate phone numbers and email addresses
per restaurant, considering whitespace and case-insensitive matching.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beeznest.settings')
django.setup()

from core.models import Customer, Restaurant

def audit_customers():
    print("=" * 80)
    print("CUSTOMER DUPLICATE AUDIT REPORT")
    print("=" * 80)
    print()

    # Get all customers
    all_customers = Customer.objects.all()
    total_customers = all_customers.count()
    print(f"Total customers in database: {total_customers}")
    print()

    # Analyze data storage patterns
    print("DATA STORAGE PATTERNS")
    print("-" * 80)
    null_phones = all_customers.filter(phone__isnull=True).count()
    blank_phones = all_customers.filter(phone='').count()
    whitespace_phones = all_customers.exclude(phone__isnull=True).exclude(phone='').filter(phone__regex=r'^\s+$').count()
    non_null_phones = total_customers - null_phones

    null_emails = all_customers.filter(email__isnull=True).count()
    blank_emails = all_customers.filter(email='').count()
    whitespace_emails = all_customers.exclude(email__isnull=True).exclude(email='').filter(email__regex=r'^\s+$').count()
    non_null_emails = total_customers - null_emails

    print(f"Phone storage:")
    print(f"  NULL values: {null_phones}")
    print(f"  Empty strings (''): {blank_phones}")
    print(f"  Whitespace-only strings: {whitespace_phones}")
    print(f"  Non-NULL values: {non_null_phones}")
    print()
    print(f"Email storage:")
    print(f"  NULL values: {null_emails}")
    print(f"  Empty strings (''): {blank_emails}")
    print(f"  Whitespace-only strings: {whitespace_emails}")
    print(f"  Non-NULL values: {non_null_emails}")
    print()

    # Check for duplicate phone numbers per restaurant
    print("DUPLICATE PHONE NUMBERS (by restaurant)")
    print("-" * 80)
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
        print(f"Found {len(phone_duplicates)} duplicate phone groups:")
        for dup in phone_duplicates:
            print(f"  Restaurant: {dup['restaurant_name']} (ID: {dup['restaurant_id']})")
            print(f"    Phone (masked): {dup['phone_masked']}")
            print(f"    Duplicate count: {dup['count']}")
            print(f"    Customer IDs: {dup['customer_ids']}")
            print()
    else:
        print("No duplicate phone numbers found.")
    print()

    # Check for duplicate email addresses per restaurant (case-insensitive)
    print("DUPLICATE EMAIL ADDRESSES (by restaurant, case-insensitive)")
    print("-" * 80)
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
        print(f"Found {len(email_duplicates)} duplicate email groups:")
        for dup in email_duplicates:
            print(f"  Restaurant: {dup['restaurant_name']} (ID: {dup['restaurant_id']})")
            print(f"    Email (masked): {dup['email_masked']}")
            print(f"    Duplicate count: {dup['count']}")
            print(f"    Customer IDs: {dup['customer_ids']}")
            print()
    else:
        print("No duplicate email addresses found.")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total customers: {total_customers}")
    print(f"Total restaurants: {restaurants.count()}")
    print(f"Duplicate phone groups: {len(phone_duplicates)}")
    print(f"Duplicate email groups: {len(email_duplicates)}")
    print()

    # Constraint implications
    print("CONSTRAINT IMPLICATIONS")
    print("-" * 80)
    if phone_duplicates or email_duplicates:
        print("WARNING: Existing duplicates found.")
        print("Adding conditional unique constraints (restaurant, phone) and (restaurant, email)")
        print("would fail due to existing duplicate records.")
        print()
        print("The constraints would need to be:")
        print("  - Partial unique index on (restaurant_id, phone) WHERE phone IS NOT NULL AND phone != ''")
        print("  - Partial unique index on (restaurant_id, email) WHERE email IS NOT NULL AND email != ''")
        print()
        print("Current duplicate handling in order creation:")
        print("  - Phone: Uses .first() to get existing customer, updates name/email if provided")
        print("  - Email: No deduplication logic on email alone")
        print("  - This can lead to multiple customers with same email but different phones")
    else:
        print("No duplicates found. Conditional unique constraints can be safely added.")
    print()

    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    audit_customers()
