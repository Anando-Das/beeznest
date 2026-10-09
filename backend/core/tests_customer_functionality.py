"""
Tests for customer duplicate prevention (Phase 1B) and customer search (Phase 2).
Tests database-level constraints, application-level validation, and search functionality.
"""

from django.test import TestCase
from unittest import skipIf
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db import connection
from .models import Restaurant, Customer, Table, Category, MenuItem, Zone, Order, OrderItem, Payment

User = get_user_model()


class CustomerDuplicatePreventionTestCase(TestCase):
    """Test customer duplicate prevention at database and application levels."""

    def setUp(self):
        self.restaurant1 = Restaurant.objects.create(name="Restaurant 1")
        self.restaurant2 = Restaurant.objects.create(name="Restaurant 2")

        self.manager1 = User.objects.create_user(
            username="manager1", password="password", role="MANAGER", restaurant=self.restaurant1
        )
        self.manager2 = User.objects.create_user(
            username="manager2", password="password", role="MANAGER", restaurant=self.restaurant2
        )

        self.client = APIClient()

    def test_duplicate_phone_within_same_restaurant_fails(self):
        """Test that creating a customer with duplicate phone in same restaurant fails."""
        self.client.force_authenticate(user=self.manager1)

        # Create first customer
        response1 = self.client.post('/api/auth/customers/', {
            'name': 'Customer One',
            'phone': '01700000000',
            'email': 'customer1@example.com'
        }, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Try to create second customer with same phone
        response2 = self.client.post('/api/auth/customers/', {
            'name': 'Customer Two',
            'phone': '01700000000',
            'email': 'customer2@example.com'
        }, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        # Error may be in 'phone' field or 'detail' depending on whether serializer or DB constraint catches it
        self.assertTrue('phone' in response2.data or 'detail' in response2.data)

    def test_duplicate_phone_with_whitespace_fails(self):
        """Test that phone with leading/trailing whitespace is normalized and duplicate check works."""
        self.client.force_authenticate(user=self.manager1)

        # Create first customer with phone
        response1 = self.client.post('/api/auth/customers/', {
            'name': 'Customer One',
            'phone': ' 01700000000  ',
            'email': 'customer1@example.com'
        }, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Try to create second customer with same phone (different whitespace)
        response2 = self.client.post('/api/auth/customers/', {
            'name': 'Customer Two',
            'phone': '01700000000',
            'email': 'customer2@example.com'
        }, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('phone' in response2.data or 'detail' in response2.data)

    def test_duplicate_email_case_insensitive_fails(self):
        """Test that email comparison is case-insensitive."""
        self.client.force_authenticate(user=self.manager1)

        # Create first customer with lowercase email
        response1 = self.client.post('/api/auth/customers/', {
            'name': 'Customer One',
            'phone': '01700000001',
            'email': 'test@example.com'
        }, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Try to create second customer with uppercase email
        response2 = self.client.post('/api/auth/customers/', {
            'name': 'Customer Two',
            'phone': '01700000002',
            'email': 'TEST@EXAMPLE.COM'
        }, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('email' in response2.data or 'detail' in response2.data)

    def test_null_and_empty_contact_values_allowed(self):
        """Test that NULL and empty contact values are allowed."""
        self.client.force_authenticate(user=self.manager1)

        # Create customer with null phone and email
        response1 = self.client.post('/api/auth/customers/', {
            'name': 'Customer One',
            'phone': '',
            'email': ''
        }, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Create another customer with null phone and email (should be allowed)
        response2 = self.client.post('/api/auth/customers/', {
            'name': 'Customer Two',
            'phone': '',
            'email': ''
        }, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Create customer with only phone
        response3 = self.client.post('/api/auth/customers/', {
            'name': 'Customer Three',
            'phone': '01700000003',
            'email': ''
        }, format='json')
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)

        # Create customer with only email
        response4 = self.client.post('/api/auth/customers/', {
            'name': 'Customer Four',
            'phone': '',
            'email': 'customer4@example.com'
        }, format='json')
        self.assertEqual(response4.status_code, status.HTTP_201_CREATED)

    def test_same_contact_different_restaurants_allowed(self):
        """Test that same phone/email in different restaurants is allowed."""
        self.client.force_authenticate(user=self.manager1)

        # Create customer in restaurant1
        response1 = self.client.post('/api/auth/customers/', {
            'name': 'Customer One',
            'phone': '01700000000',
            'email': 'customer@example.com'
        }, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Create customer with same contact in restaurant2
        self.client.force_authenticate(user=self.manager2)
        response2 = self.client.post('/api/auth/customers/', {
            'name': 'Customer Two',
            'phone': '01700000000',
            'email': 'customer@example.com'
        }, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

    def test_update_customer_to_duplicate_phone_fails(self):
        """Test that updating a customer to duplicate phone fails."""
        self.client.force_authenticate(user=self.manager1)

        # Create two customers with different phones
        customer1 = Customer.objects.create(
            restaurant=self.restaurant1,
            name='Customer One',
            phone='01700000001',
            email='customer1@example.com'
        )
        customer2 = Customer.objects.create(
            restaurant=self.restaurant1,
            name='Customer Two',
            phone='01700000002',
            email='customer2@example.com'
        )

        # Try to update customer2 to have customer1's phone
        response = self.client.put(f'/api/auth/customers/{customer2.id}/', {
            'name': 'Customer Two Updated',
            'phone': '01700000001',
            'email': 'customer2@example.com'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('phone' in response.data or 'detail' in response.data)

    def test_update_customer_to_duplicate_email_fails(self):
        """Test that updating a customer to duplicate email fails."""
        self.client.force_authenticate(user=self.manager1)

        # Create two customers with different emails
        customer1 = Customer.objects.create(
            restaurant=self.restaurant1,
            name='Customer One',
            phone='01700000001',
            email='customer1@example.com'
        )
        customer2 = Customer.objects.create(
            restaurant=self.restaurant1,
            name='Customer Two',
            phone='01700000002',
            email='customer2@example.com'
        )

        # Try to update customer2 to have customer1's email
        response = self.client.put(f'/api/auth/customers/{customer2.id}/', {
            'name': 'Customer Two Updated',
            'phone': '01700000002',
            'email': 'CUSTOMER1@EXAMPLE.COM'  # Case-insensitive
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('email' in response.data or 'detail' in response.data)

    def test_order_creation_with_duplicate_phone_updates_existing(self):
        """Test that order creation with existing phone updates the customer."""
        self.client.force_authenticate(user=self.manager1)

        # Setup: Create category, menu item, table
        zone = Zone.objects.create(restaurant=self.restaurant1, name="Zone 1", is_active=True)
        table = Table.objects.create(restaurant=self.restaurant1, name="Table 1", zone=zone, is_active=True)
        category = Category.objects.create(restaurant=self.restaurant1, name="Food", is_active=True)
        menu_item = MenuItem.objects.create(
            category=category, name="Burger", price=100.00, is_available=True
        )

        # Create initial customer
        existing_customer = Customer.objects.create(
            restaurant=self.restaurant1,
            name='Original Name',
            phone='01700000000',
            email='original@example.com'
        )

        # Create order with same phone but different name/email
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': table.id,
            'order_type': 'dine-in',
            'customer_phone': '01700000000',
            'customer_name': 'Updated Name',
            'customer_email': 'updated@example.com',
            'items': [
                {'menu_item': menu_item.id, 'quantity': 1}
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify customer was updated, not duplicated
        existing_customer.refresh_from_db()
        self.assertEqual(existing_customer.name, 'Updated Name')
        self.assertEqual(existing_customer.email, 'updated@example.com')
        self.assertEqual(Customer.objects.filter(restaurant=self.restaurant1, phone='01700000000').count(), 1)

    @skipIf(connection.vendor == 'sqlite', "SQLite doesn't support MariaDB virtual columns")
    def test_database_constraint_enforcement(self):
        """Test that database-level constraints are enforced."""
        # This test bypasses Django ORM to test database constraints directly
        # Only runs on MariaDB/MySQL, not SQLite test database

        customer1 = Customer.objects.create(
            restaurant=self.restaurant1,
            name='Customer One',
            phone='01700000000',
            email='customer1@example.com'
        )

        # Try to create duplicate using raw SQL (should fail)
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT INTO core_customer (restaurant_id, name, phone, email, points, created_at)
                    VALUES (%s, %s, %s, %s, 0, NOW())
                """, [self.restaurant1.id, 'Customer Two', '01700000000', 'customer2@example.com'])
                self.fail("Database constraint should have prevented duplicate phone")
            except IntegrityError:
                # Expected - constraint worked
                pass

        # Verify only one customer exists
        self.assertEqual(Customer.objects.filter(restaurant=self.restaurant1, phone='01700000000').count(), 1)


class CustomerSearchTestCase(TestCase):
    """Test customer search API (Phase 2)."""

    def setUp(self):
        self.restaurant1 = Restaurant.objects.create(name="Restaurant 1")
        self.restaurant2 = Restaurant.objects.create(name="Restaurant 2")

        self.manager1 = User.objects.create_user(
            username="manager1", password="password", role="MANAGER", restaurant=self.restaurant1
        )
        self.cashier1 = User.objects.create_user(
            username="cashier1", password="password", role="CASHIER", restaurant=self.restaurant1
        )
        self.waiter1 = User.objects.create_user(
            username="waiter1", password="password", role="WAITER", restaurant=self.restaurant1
        )
        self.manager2 = User.objects.create_user(
            username="manager2", password="password", role="MANAGER", restaurant=self.restaurant2
        )

        # Create customers in restaurant1
        self.customer1 = Customer.objects.create(
            restaurant=self.restaurant1,
            name='John Doe',
            phone='01700000001',
            email='john@example.com'
        )
        self.customer2 = Customer.objects.create(
            restaurant=self.restaurant1,
            name='Jane Smith',
            phone='01700000002',
            email='jane@example.com'
        )
        self.customer3 = Customer.objects.create(
            restaurant=self.restaurant1,
            name='Bob Johnson',
            phone='01800000001',
            email='bob@example.com'
        )

        # Create customer in restaurant2 (should not appear in restaurant1 searches)
        self.customer4 = Customer.objects.create(
            restaurant=self.restaurant2,
            name='Other Customer',
            phone='01700000001',
            email='other@example.com'
        )

        self.client = APIClient()

    def test_search_by_phone_partial_match(self):
        """Test searching by partial phone number."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'phone': '017'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # customer1 and customer2
        returned_ids = [c['id'] for c in response.data]
        self.assertIn(self.customer1.id, returned_ids)
        self.assertIn(self.customer2.id, returned_ids)
        self.assertNotIn(self.customer3.id, returned_ids)

    def test_search_by_phone_exact_match(self):
        """Test searching by exact phone number."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'phone': '01700000001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.customer1.id)
        self.assertEqual(response.data[0]['name'], 'John Doe')

    def test_search_by_email_partial_match(self):
        """Test searching by partial email address."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'email': 'john'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.customer1.id)

    def test_search_by_email_case_insensitive(self):
        """Test that email search is case-insensitive."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'email': 'JOHN@EXAMPLE.COM'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.customer1.id)

    def test_search_by_email_exact_match(self):
        """Test searching by exact email address."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'email': 'jane@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.customer2.id)

    def test_search_by_phone_and_email(self):
        """Test searching by both phone and email (AND logic)."""
        self.client.force_authenticate(user=self.manager1)

        # Should only return customer1 (matches both phone prefix and email prefix)
        response = self.client.get('/api/auth/customers/search/', {'phone': '017', 'email': 'john'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.customer1.id)

    def test_search_without_parameters_fails(self):
        """Test that search requires at least one parameter."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('search parameter', response.data['detail'])

    def test_search_with_short_phone_fails(self):
        """Test that phone search requires minimum 3 characters."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'phone': '01'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('at least 3 characters', response.data['detail'])

    def test_search_with_short_email_fails(self):
        """Test that email search requires minimum 3 characters."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'email': 'ab'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('at least 3 characters', response.data['detail'])

    def test_search_restaurant_isolation(self):
        """Test that search only returns customers from the authenticated user's restaurant."""
        self.client.force_authenticate(user=self.manager1)

        # Search for phone that exists in both restaurants
        response = self.client.get('/api/auth/customers/search/', {'phone': '01700000001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # Should only return restaurant1's customer, not restaurant2's
        self.assertEqual(response.data[0]['id'], self.customer1.id)
        self.assertNotEqual(response.data[0]['id'], self.customer4.id)

    def test_search_unauthenticated_fails(self):
        """Test that unauthenticated users cannot search."""
        response = self.client.get('/api/auth/customers/search/', {'phone': '017'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_result_limit(self):
        """Test that search results are limited to 10."""
        self.client.force_authenticate(user=self.manager1)

        # Create additional customers to test limit
        for i in range(15):
            Customer.objects.create(
                restaurant=self.restaurant1,
                name=f'Customer {i}',
                phone=f'019000000{i:02d}',
                email=f'customer{i}@example.com'
            )

        response = self.client.get('/api/auth/customers/search/', {'phone': '019'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 10)

    def test_search_returns_only_required_fields(self):
        """Test that search returns only id, name, phone, email fields."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'phone': '017'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if response.data:
            # Check that only required fields are present
            allowed_fields = {'id', 'name', 'phone', 'email'}
            for customer in response.data:
                self.assertEqual(set(customer.keys()), allowed_fields)

    def test_search_with_whitespace_normalization(self):
        """Test that search normalizes whitespace in parameters."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'phone': ' 017 '})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_search_permissions_cashier(self):
        """Test that cashier role can search customers."""
        self.client.force_authenticate(user=self.cashier1)

        response = self.client.get('/api/auth/customers/search/', {'phone': '017'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_permissions_waiter(self):
        """Test that waiter role can search customers."""
        self.client.force_authenticate(user=self.waiter1)

        response = self.client.get('/api/auth/customers/search/', {'phone': '017'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_no_results(self):
        """Test search that returns no results."""
        self.client.force_authenticate(user=self.manager1)

        response = self.client.get('/api/auth/customers/search/', {'phone': '999'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class OrderCustomerLinkingTestCase(TestCase):
    """Test order creation with customer_id (Phase 3 backend support)."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        self.manager = User.objects.create_user(
            username="manager", password="password", role="MANAGER", restaurant=self.restaurant
        )

        self.zone = Zone.objects.create(restaurant=self.restaurant, name="Zone 1", is_active=True)
        self.table = Table.objects.create(restaurant=self.restaurant, name="Table 1", zone=self.zone, is_active=True)
        self.category = Category.objects.create(restaurant=self.restaurant, name="Food", is_active=True)
        self.menu_item = MenuItem.objects.create(
            category=self.category, name="Burger", price=100.00, is_available=True
        )

        self.customer = Customer.objects.create(
            restaurant=self.restaurant,
            name='Existing Customer',
            phone='01700000000',
            email='existing@example.com'
        )

        self.client = APIClient()

    def test_create_order_with_customer_id(self):
        """Test creating an order with a customer_id links to the correct customer."""
        self.client.force_authenticate(user=self.manager)

        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'order_type': 'dine-in',
            'customer_id': self.customer.id,
            'items': [
                {'menu_item': self.menu_item.id, 'quantity': 1}
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify order is linked to the correct customer
        created_order = Order.objects.get(id=response.data['id'])
        self.assertEqual(created_order.customer, self.customer)
        self.assertEqual(created_order.customer.name, 'Existing Customer')

    def test_create_order_with_customer_id_ignores_phone_name_email(self):
        """Test that customer_id takes precedence over phone/name/email fields."""
        self.client.force_authenticate(user=self.manager)

        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'order_type': 'dine-in',
            'customer_id': self.customer.id,
            'customer_phone': '99999999999',  # Different phone
            'customer_name': 'Different Name',  # Different name
            'customer_email': 'different@example.com',  # Different email
            'items': [
                {'menu_item': self.menu_item.id, 'quantity': 1}
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify customer was not updated
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.phone, '01700000000')
        self.assertEqual(self.customer.name, 'Existing Customer')
        self.assertEqual(self.customer.email, 'existing@example.com')

    def test_create_order_with_invalid_customer_id_fails(self):
        """Test that invalid customer_id is rejected."""
        self.client.force_authenticate(user=self.manager)

        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'order_type': 'dine-in',
            'customer_id': 99999,  # Non-existent customer
            'items': [
                {'menu_item': self.menu_item.id, 'quantity': 1}
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer_id', response.data)

    def test_create_order_with_customer_id_from_different_restaurant_fails(self):
        """Test that customer_id from different restaurant is rejected."""
        other_restaurant = Restaurant.objects.create(name="Other Restaurant")
        other_customer = Customer.objects.create(
            restaurant=other_restaurant,
            name='Other Customer',
            phone='01800000000',
            email='other@example.com'
        )

        self.client.force_authenticate(user=self.manager)

        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'order_type': 'dine-in',
            'customer_id': other_customer.id,
            'items': [
                {'menu_item': self.menu_item.id, 'quantity': 1}
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer_id', response.data)

    def test_create_order_without_customer_id_still_works(self):
        """Test that order creation without customer_id still works (backward compatibility)."""
        self.client.force_authenticate(user=self.manager)

        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'order_type': 'dine-in',
            'customer_phone': '01900000000',
            'customer_name': 'New Customer',
            'items': [
                {'menu_item': self.menu_item.id, 'quantity': 1}
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify new customer was created
        created_order = Order.objects.get(id=response.data['id'])
        self.assertIsNotNone(created_order.customer)
        self.assertEqual(created_order.customer.name, 'New Customer')
        self.assertEqual(created_order.customer.phone, '01900000000')


class CustomerOrderHistoryTestCase(TestCase):
    """Test customer order history API (Phase 4)."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        self.manager = User.objects.create_user(
            username="manager", password="password", role="MANAGER", restaurant=self.restaurant
        )
        self.cashier = User.objects.create_user(
            username="cashier", password="password", role="CASHIER", restaurant=self.restaurant
        )

        self.zone = Zone.objects.create(restaurant=self.restaurant, name="Zone 1", is_active=True)
        self.table = Table.objects.create(restaurant=self.restaurant, name="Table 1", zone=self.zone, is_active=True)
        self.category = Category.objects.create(restaurant=self.restaurant, name="Food", is_active=True)
        self.menu_item1 = MenuItem.objects.create(
            category=self.category, name="Burger", price=100.00, is_available=True
        )
        self.menu_item2 = MenuItem.objects.create(
            category=self.category, name="Fries", price=50.00, is_available=True
        )

        self.customer = Customer.objects.create(
            restaurant=self.restaurant,
            name='Test Customer',
            phone='01700000000',
            email='test@example.com'
        )

        self.client = APIClient()

    def test_customer_order_history_retrieval(self):
        """Test retrieving order history for a customer."""
        self.client.force_authenticate(user=self.manager)

        # Create some orders for the customer
        order1 = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='paid',
            total_amount=150.00
        )
        OrderItem.objects.create(
            order=order1,
            menu_item=self.menu_item1,
            quantity=1,
            price_at_time=100.00
        )
        OrderItem.objects.create(
            order=order1,
            menu_item=self.menu_item2,
            quantity=1,
            price_at_time=50.00
        )

        # Create payment for order1
        Payment.objects.create(
            order=order1,
            amount=150.00,
            method='cash',
            processed_by=self.manager
        )

        order2 = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            order_type='takeaway',
            status='open',
            total_amount=100.00
        )
        OrderItem.objects.create(
            order=order2,
            menu_item=self.menu_item1,
            quantity=1,
            price_at_time=100.00
        )

        # Fetch order history
        response = self.client.get(f'/api/auth/customers/{self.customer.id}/order_history/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.customer.id)
        self.assertEqual(response.data['name'], 'Test Customer')
        self.assertEqual(response.data['total_orders'], 2)
        self.assertEqual(float(response.data['total_spending']), 150.00)  # Only paid orders
        self.assertEqual(len(response.data['orders']), 2)

        # Verify orders are returned with correct data
        orders = response.data['orders']
        self.assertEqual(len(orders), 2)

        # Check first order (should be most recent)
        first_order = orders[0]
        self.assertEqual(first_order['id'], order2.id)
        self.assertEqual(first_order['order_type'], 'takeaway')
        self.assertEqual(first_order['status'], 'open')
        self.assertEqual(len(first_order['items']), 1)
        self.assertEqual(first_order['items'][0]['menu_item_name'], 'Burger')
        self.assertIsNone(first_order['payment_method'])  # Not paid

        # Check second order
        second_order = orders[1]
        self.assertEqual(second_order['id'], order1.id)
        self.assertEqual(second_order['order_type'], 'dine-in')
        self.assertEqual(second_order['status'], 'paid')
        self.assertEqual(len(second_order['items']), 2)
        self.assertEqual(second_order['payment_method'], 'cash')
        self.assertEqual(float(second_order['payment_amount']), 150.00)

    def test_customer_with_no_orders(self):
        """Test order history for a customer with no orders."""
        self.client.force_authenticate(user=self.manager)

        response = self.client.get(f'/api/auth/customers/{self.customer.id}/order_history/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_orders'], 0)
        self.assertEqual(float(response.data['total_spending']), 0)
        self.assertIsNone(response.data['most_recent_order_date'])
        self.assertEqual(len(response.data['orders']), 0)

    def test_order_history_restaurant_isolation(self):
        """Test that order history respects restaurant isolation."""
        other_restaurant = Restaurant.objects.create(name="Other Restaurant")
        other_customer = Customer.objects.create(
            restaurant=other_restaurant,
            name='Other Customer',
            phone='01800000000'
        )

        # Create order for other customer
        other_order = Order.objects.create(
            restaurant=other_restaurant,
            customer=other_customer,
            order_type='takeaway',
            status='paid',
            total_amount=200.00
        )

        self.client.force_authenticate(user=self.manager)

        # Try to access other restaurant's customer order history
        response = self.client.get(f'/api/auth/customers/{other_customer.id}/order_history/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_history_permissions(self):
        """Test that appropriate roles can access order history."""
        # Create an order for the customer
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='paid',
            total_amount=100.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item1,
            quantity=1,
            price_at_time=100.00
        )

        # Manager should have access
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(f'/api/auth/customers/{self.customer.id}/order_history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Cashier should have access
        self.client.force_authenticate(user=self.cashier)
        response = self.client.get(f'/api/auth/customers/{self.customer.id}/order_history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Unauthenticated should not have access
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/auth/customers/{self.customer.id}/order_history/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_history_unpaid_orders_not_counted_in_spending(self):
        """Test that unpaid orders are not included in total spending."""
        self.client.force_authenticate(user=self.manager)

        # Create paid order
        paid_order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='paid',
            total_amount=100.00
        )
        OrderItem.objects.create(
            order=paid_order,
            menu_item=self.menu_item1,
            quantity=1,
            price_at_time=100.00
        )
        Payment.objects.create(
            order=paid_order,
            amount=100.00,
            method='cash',
            processed_by=self.manager
        )

        # Create unpaid order
        unpaid_order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            order_type='takeaway',
            status='open',
            total_amount=200.00
        )
        OrderItem.objects.create(
            order=unpaid_order,
            menu_item=self.menu_item1,
            quantity=2,
            price_at_time=100.00
        )

        response = self.client.get(f'/api/auth/customers/{self.customer.id}/order_history/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_orders'], 2)
        self.assertEqual(float(response.data['total_spending']), 100.00)  # Only paid order

    def test_order_history_with_notes(self):
        """Test that order item notes are included in history."""
        self.client.force_authenticate(user=self.manager)

        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='paid',
            total_amount=100.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item1,
            quantity=1,
            price_at_time=100.00,
            notes='No onions please'
        )

        response = self.client.get(f'/api/auth/customers/{self.customer.id}/order_history/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['orders'][0]['items'][0]['notes'], 'No onions please')

    def test_orders_without_customer_unaffected(self):
        """Test that orders without a linked customer are not affected."""
        self.client.force_authenticate(user=self.manager)

        # Create order without customer
        order_no_customer = Order.objects.create(
            restaurant=self.restaurant,
            customer=None,
            table=self.table,
            order_type='dine-in',
            status='paid',
            total_amount=100.00
        )
        OrderItem.objects.create(
            order=order_no_customer,
            menu_item=self.menu_item1,
            quantity=1,
            price_at_time=100.00
        )

        # Customer order history should not include this order
        response = self.client.get(f'/api/auth/customers/{self.customer.id}/order_history/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_orders'], 0)
        self.assertEqual(len(response.data['orders']), 0)

        # Order should still exist and be retrievable
        self.assertIsNotNone(Order.objects.get(id=order_no_customer.id))
