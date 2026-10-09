"""
Tests for Customer Loyalty Points System.
Tests loyalty settings, point earning, redemption, cancellation reversals, and expiry.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Restaurant, Customer, Table, Category, MenuItem, Zone, Order, OrderItem, Payment, LoyaltySettings, PointTransaction

User = get_user_model()


class LoyaltySettingsTestCase(TestCase):
    """Test loyalty settings API and restaurant isolation."""

    def setUp(self):
        self.restaurant1 = Restaurant.objects.create(name="Restaurant 1")
        self.restaurant2 = Restaurant.objects.create(name="Restaurant 2")

        self.owner1 = User.objects.create_user(
            username="owner1", password="password", role="OWNER", restaurant=self.restaurant1
        )
        self.manager1 = User.objects.create_user(
            username="manager1", password="password", role="MANAGER", restaurant=self.restaurant1
        )
        self.cashier1 = User.objects.create_user(
            username="cashier1", password="password", role="CASHIER", restaurant=self.restaurant1
        )
        self.owner2 = User.objects.create_user(
            username="owner2", password="password", role="OWNER", restaurant=self.restaurant2
        )

        self.client = APIClient()

    def test_get_or_create_loyalty_settings(self):
        """Test that loyalty settings are created on first access."""
        self.client.force_authenticate(user=self.owner1)

        response = self.client.get('/api/auth/loyalty-settings/my_settings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['enabled'], False)
        self.assertEqual(float(response.data['points_earning_rate']), 100.00)
        self.assertEqual(float(response.data['points_redemption_rate']), 1.00)
        self.assertIsNone(response.data['points_expiry_days'])

    def test_update_loyalty_settings(self):
        """Test updating loyalty settings."""
        self.client.force_authenticate(user=self.owner1)

        # First get the settings to get the ID
        response = self.client.get('/api/auth/loyalty-settings/my_settings/')
        settings_id = response.data['id']

        response = self.client.patch(f'/api/auth/loyalty-settings/{settings_id}/', {
            'enabled': True,
            'points_earning_rate': 50.00,
            'points_redemption_rate': 0.50,
            'points_expiry_days': 365
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['enabled'], True)
        self.assertEqual(float(response.data['points_earning_rate']), 50.00)
        self.assertEqual(float(response.data['points_redemption_rate']), 0.50)
        self.assertEqual(response.data['points_expiry_days'], 365)

    def test_loyalty_settings_restaurant_isolation(self):
        """Test that loyalty settings are isolated per restaurant."""
        self.client.force_authenticate(user=self.owner1)

        # Get settings ID for restaurant1
        response = self.client.get('/api/auth/loyalty-settings/my_settings/')
        settings_id = response.data['id']

        # Update restaurant1 settings
        self.client.patch(f'/api/auth/loyalty-settings/{settings_id}/', {
            'enabled': True,
            'points_earning_rate': 50.00
        }, format='json')

        # Switch to restaurant2
        self.client.force_authenticate(user=self.owner2)
        response = self.client.get('/api/auth/loyalty-settings/my_settings/')

        # Should have default settings, not restaurant1's settings
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['enabled'], False)
        self.assertEqual(float(response.data['points_earning_rate']), 100.00)

    def test_loyalty_settings_permissions(self):
        """Test that only OWNER and MANAGER can write to loyalty settings."""
        # Create settings
        self.client.force_authenticate(user=self.owner1)
        response = self.client.get('/api/auth/loyalty-settings/my_settings/')
        settings_id = response.data['id']

        self.client.patch(f'/api/auth/loyalty-settings/{settings_id}/', {'enabled': True}, format='json')

        # Manager should be able to read
        self.client.force_authenticate(user=self.manager1)
        response = self.client.get('/api/auth/loyalty-settings/my_settings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Manager should be able to write
        response = self.client.patch(f'/api/auth/loyalty-settings/{settings_id}/', {
            'points_earning_rate': 75.00
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Cashier should be able to read
        self.client.force_authenticate(user=self.cashier1)
        response = self.client.get('/api/auth/loyalty-settings/my_settings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Cashier should NOT be able to write
        response = self.client.patch(f'/api/auth/loyalty-settings/{settings_id}/', {
            'enabled': False
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PointEarningTestCase(TestCase):
    """Test point earning on payment."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        self.owner = User.objects.create_user(
            username="owner", password="password", role="OWNER", restaurant=self.restaurant
        )
        self.cashier = User.objects.create_user(
            username="cashier", password="password", role="CASHIER", restaurant=self.restaurant
        )

        self.zone = Zone.objects.create(restaurant=self.restaurant, name="Zone 1", is_active=True)
        self.table = Table.objects.create(restaurant=self.restaurant, name="Table 1", zone=self.zone, is_active=True)
        self.category = Category.objects.create(restaurant=self.restaurant, name="Food", is_active=True)
        self.menu_item = MenuItem.objects.create(
            category=self.category, name="Burger", price=100.00, is_available=True
        )

        self.customer = Customer.objects.create(
            restaurant=self.restaurant,
            name='Test Customer',
            phone='01700000000'
        )

        self.client = APIClient()

    def test_points_earned_on_payment(self):
        """Test that points are earned after successful payment."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty with 100 currency = 1 point
        loyalty_settings = LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00,
            points_redemption_rate=1.00
        )

        # Create and pay order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        response = self.client.post(f'/api/auth/orders/{order.id}/pay/', {
            'method': 'cash'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify points were earned (500 / 100 = 5 points)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 5)

        # Verify transaction was created
        transactions = PointTransaction.objects.filter(
            customer=self.customer,
            transaction_type='EARNED'
        )
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().points, 5)
        self.assertEqual(transactions.first().balance_after, 5)

    def test_points_not_earned_when_disabled(self):
        """Test that points are not earned when loyalty is disabled."""
        self.client.force_authenticate(user=self.owner)

        # Disable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=False,
            points_earning_rate=100.00
        )

        # Create and pay order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        self.client.post(f'/api/auth/orders/{order.id}/pay/', {
            'method': 'cash'
        }, format='json')

        # Verify no points were earned
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 0)

    def test_points_not_earned_for_order_without_customer(self):
        """Test that points are not earned for orders without a customer."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00
        )

        # Create order without customer
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=None,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        self.client.post(f'/api/auth/orders/{order.id}/pay/', {
            'method': 'cash'
        }, format='json')

        # Verify no transactions were created
        transactions = PointTransaction.objects.filter(transaction_type='EARNED')
        self.assertEqual(transactions.count(), 0)

    def test_duplicate_payment_awards_points_only_once(self):
        """Test that duplicate payment attempts don't award points twice (idempotency)."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00
        )

        # Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        # Pay once
        self.client.post(f'/api/auth/orders/{order.id}/pay/', {
            'method': 'cash'
        }, format='json')

        self.customer.refresh_from_db()
        points_after_first = self.customer.points

        # Try to pay again (should fail as order is already paid)
        response = self.client.post(f'/api/auth/orders/{order.id}/pay/', {
            'method': 'cash'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify points weren't awarded twice
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, points_after_first)

        # Verify only one EARNED transaction exists
        transactions = PointTransaction.objects.filter(
            customer=self.customer,
            transaction_type='EARNED'
        )
        self.assertEqual(transactions.count(), 1)


class PointRedemptionTestCase(TestCase):
    """Test point redemption."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        self.owner = User.objects.create_user(
            username="owner", password="password", role="OWNER", restaurant=self.restaurant
        )
        self.cashier = User.objects.create_user(
            username="cashier", password="password", role="CASHIER", restaurant=self.restaurant
        )

        self.zone = Zone.objects.create(restaurant=self.restaurant, name="Zone 1", is_active=True)
        self.table = Table.objects.create(restaurant=self.restaurant, name="Table 1", zone=self.zone, is_active=True)
        self.category = Category.objects.create(restaurant=self.restaurant, name="Food", is_active=True)
        self.menu_item = MenuItem.objects.create(
            category=self.category, name="Burger", price=100.00, is_available=True
        )

        self.customer = Customer.objects.create(
            restaurant=self.restaurant,
            name='Test Customer',
            phone='01700000000',
            points=100  # Start with 100 points
        )

        self.client = APIClient()

    def test_redeem_points_success(self):
        """Test successful point redemption."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty: 1 point = 1 currency
        loyalty_settings = LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00,
            points_redemption_rate=1.00
        )

        # Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        # Redeem 50 points
        response = self.client.post('/api/auth/point-transactions/redeem/', {
            'points_to_redeem': 50,
            'order_id': order.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['points_redeemed'], 50)
        self.assertEqual(response.data['discount_amount'], 50.00)
        self.assertEqual(response.data['customer_balance_after_redemption'], 50)
        self.assertEqual(response.data['final_order_total'], 450.00)
        self.assertEqual(response.data['payment_processed'], False)

        # Verify customer balance
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 50)

        # Verify order total
        order.refresh_from_db()
        self.assertEqual(float(order.total_amount), 450.00)

        # Verify transaction was created
        transactions = PointTransaction.objects.filter(
            customer=self.customer,
            transaction_type='REDEEMED'
        )
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().points, -50)
        self.assertEqual(transactions.first().balance_after, 50)

    def test_redeem_insufficient_points(self):
        """Test redemption with insufficient points."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_redemption_rate=1.00
        )

        # Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )

        # Try to redeem more points than available
        response = self.client.post('/api/auth/point-transactions/redeem/', {
            'points_to_redeem': 150,
            'order_id': order.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient points', response.data['detail'])

    def test_redeem_when_loyalty_disabled(self):
        """Test that redemption fails when loyalty is disabled."""
        self.client.force_authenticate(user=self.owner)

        # Disable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=False
        )

        # Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )

        # Try to redeem
        response = self.client.post('/api/auth/point-transactions/redeem/', {
            'points_to_redeem': 50,
            'order_id': order.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not enabled', response.data['detail'])

    def test_redeem_duplicate_prevention(self):
        """Test that points can only be redeemed once per order."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_redemption_rate=1.00
        )

        # Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )

        # Redeem once
        self.client.post('/api/auth/point-transactions/redeem/', {
            'points_to_redeem': 50,
            'order_id': order.id
        }, format='json')

        # Try to redeem again
        response = self.client.post('/api/auth/point-transactions/redeem/', {
            'points_to_redeem': 25,
            'order_id': order.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been redeemed', response.data['detail'])

    def test_redeem_with_payment_success(self):
        """Test successful point redemption with atomic payment processing."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty: 1 point = 1 currency, 100 currency = 1 point
        loyalty_settings = LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00,
            points_redemption_rate=1.00
        )

        # Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        # Redeem 50 points and pay with cash
        response = self.client.post('/api/auth/point-transactions/redeem/', {
            'points_to_redeem': 50,
            'order_id': order.id,
            'payment_method': 'cash'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['points_redeemed'], 50)
        self.assertEqual(response.data['discount_amount'], 50.00)
        self.assertEqual(response.data['payment_processed'], True)
        self.assertEqual(response.data['payment_method'], 'cash')

        # Verify customer balance (100 - 50 = 50, then earns 4 points from 450/100 = 4)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 54)  # 50 after redemption + 4 earned

        # Verify order is paid
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertEqual(float(order.total_amount), 450.00)

        # Verify payment was created
        self.assertTrue(hasattr(order, 'payment'))
        self.assertEqual(order.payment.method, 'cash')
        self.assertEqual(float(order.payment.amount), 450.00)

        # Verify redemption transaction was created
        redemption_tx = PointTransaction.objects.filter(
            customer=self.customer,
            transaction_type='REDEEMED'
        )
        self.assertEqual(redemption_tx.count(), 1)
        self.assertEqual(redemption_tx.first().points, -50)

        # Verify earning transaction was created
        earning_tx = PointTransaction.objects.filter(
            customer=self.customer,
            transaction_type='EARNED'
        )
        self.assertEqual(earning_tx.count(), 1)
        self.assertEqual(earning_tx.first().points, 4)

    def test_redeem_with_payment_invalid_method(self):
        """Test that redemption with payment fails with invalid payment method."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_redemption_rate=1.00
        )

        # Create order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )

        # Try to redeem with invalid payment method
        response = self.client.post('/api/auth/point-transactions/redeem/', {
            'points_to_redeem': 50,
            'order_id': order.id,
            'payment_method': 'invalid_method'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The error comes from serializer validation
        self.assertIn('payment_method', response.data)

        # Verify points were NOT deducted
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 100)

    def test_redeem_order_without_customer(self):
        """Test that redemption fails for orders without a customer."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_redemption_rate=1.00
        )

        # Create order without customer
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=None,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )

        # Try to redeem
        response = self.client.post('/api/auth/point-transactions/redeem/', {
            'points_to_redeem': 50,
            'order_id': order.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must have a customer', response.data['detail'])


class PointReversalTestCase(TestCase):
    """Test point reversal on order cancellation."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        self.owner = User.objects.create_user(
            username="owner", password="password", role="OWNER", restaurant=self.restaurant
        )

        self.zone = Zone.objects.create(restaurant=self.restaurant, name="Zone 1", is_active=True)
        self.table = Table.objects.create(restaurant=self.restaurant, name="Table 1", zone=self.zone, is_active=True)
        self.category = Category.objects.create(restaurant=self.restaurant, name="Food", is_active=True)
        self.menu_item = MenuItem.objects.create(
            category=self.category, name="Burger", price=100.00, is_available=True
        )

        self.customer = Customer.objects.create(
            restaurant=self.restaurant,
            name='Test Customer',
            phone='01700000000'
        )

        self.client = APIClient()

    def test_points_reversed_on_cancellation(self):
        """Test that earned points are reversed when order is cancelled."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00
        )

        # Create and pay order to earn points
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        self.client.post(f'/api/auth/orders/{order.id}/pay/', {
            'method': 'cash'
        }, format='json')

        # Verify points were earned
        self.customer.refresh_from_db()
        points_earned = self.customer.points
        self.assertEqual(points_earned, 5)

        # Cancel the order (this should reverse points)
        # First, reset order status to allow cancellation
        order.status = 'open'
        order.save()

        response = self.client.post(f'/api/auth/orders/{order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify points were reversed
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 0)

        # Verify reversal transaction was created
        reversal_tx = PointTransaction.objects.filter(
            customer=self.customer,
            transaction_type='REVERSED'
        )
        self.assertEqual(reversal_tx.count(), 1)
        self.assertEqual(reversal_tx.first().points, -5)

    def test_cancellation_no_duplicate_reversal(self):
        """Test that points are only reversed once even if cancellation is called multiple times."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00
        )

        # Create and pay order
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        self.client.post(f'/api/auth/orders/{order.id}/pay/', {
            'method': 'cash'
        }, format='json')

        # Cancel the order
        order.status = 'open'
        order.save()
        self.client.post(f'/api/auth/orders/{order.id}/cancel/')

        # Try to cancel again (should fail as already cancelled)
        response = self.client.post(f'/api/auth/orders/{order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify only one reversal transaction exists
        reversal_tx = PointTransaction.objects.filter(
            customer=self.customer,
            transaction_type='REVERSED'
        )
        self.assertEqual(reversal_tx.count(), 1)

    def test_negative_balance_prevention(self):
        """Test that reversal cannot create negative balance."""
        self.client.force_authenticate(user=self.owner)

        # Enable loyalty
        LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00
        )

        # Start customer with 0 points
        self.customer.points = 0
        self.customer.save()

        # Create and pay order to earn points
        order = Order.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            table=self.table,
            order_type='dine-in',
            status='open',
            total_amount=500.00
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=5,
            price_at_time=100.00
        )

        self.client.post(f'/api/auth/orders/{order.id}/pay/', {
            'method': 'cash'
        }, format='json')

        # Customer now has 5 points
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 5)

        # Manually reduce balance to 1 to test negative prevention
        self.customer.points = 1
        self.customer.save()

        # Cancel the order (should try to reverse 5 points but only 1 available)
        order.status = 'open'
        order.save()
        self.client.post(f'/api/auth/orders/{order.id}/cancel/')

        # Verify balance is 0 (not negative)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 0)


class PointExpiryTestCase(TestCase):
    """Test point expiry mechanism."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        self.owner = User.objects.create_user(
            username="owner", password="password", role="OWNER", restaurant=self.restaurant
        )

        self.customer = Customer.objects.create(
            restaurant=self.restaurant,
            name='Test Customer',
            phone='01700000000',
            points=100
        )

    def test_expire_loyalty_points_command(self):
        """Test the management command for expiring points."""
        # Enable loyalty with 30-day expiry
        loyalty_settings = LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00,
            points_expiry_days=30
        )

        # Start with 100 points
        self.customer.points = 100
        self.customer.save()

        # Create an expired transaction (31 days ago) - 50 points
        expired_date = timezone.now() - timedelta(days=31)
        expired_tx = PointTransaction.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            transaction_type='EARNED',
            points=50,
            balance_after=100,
            expires_at=expired_date,
            description='Test expired points'
        )

        # Create a non-expired transaction (15 days ago) - 50 points
        # expires_at should be 30 days from the transaction date (15 days ago + 30 = 15 days from now)
        transaction_date = timezone.now() - timedelta(days=15)
        active_date = transaction_date + timedelta(days=loyalty_settings.points_expiry_days)
        PointTransaction.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            transaction_type='EARNED',
            points=50,
            balance_after=100,
            expires_at=active_date,
            description='Test active points'
        )

        # Run expiry command
        from django.core.management import call_command
        call_command('expire_loyalty_points')

        # Verify only expired points were removed (50 expired, 50 remains)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 50)  # Only active points remain

        # Verify expiry transaction was created for expired transaction
        expiry_tx = PointTransaction.objects.filter(
            related_transaction=expired_tx,
            transaction_type='EXPIRED'
        )
        self.assertEqual(expiry_tx.count(), 1)
        self.assertEqual(expiry_tx.first().points, -50)

    def test_no_expiry_when_disabled(self):
        """Test that points don't expire when expiry is disabled."""
        # Enable loyalty with no expiry (None)
        loyalty_settings = LoyaltySettings.objects.create(
            restaurant=self.restaurant,
            enabled=True,
            points_earning_rate=100.00,
            points_expiry_days=None
        )

        # Create an old transaction (with expires_at even though expiry is disabled)
        old_date = timezone.now() - timedelta(days=365)
        PointTransaction.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            transaction_type='EARNED',
            points=50,
            balance_after=100,
            expires_at=old_date,
            description='Test old points'
        )

        # Run expiry command - should not process this restaurant since expiry_days is None
        from django.core.management import call_command
        call_command('expire_loyalty_points')

        # Verify points were not expired (restaurant had expiry_days=None)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.points, 100)
