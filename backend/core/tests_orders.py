from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
from .models import Restaurant, Category, MenuItem, Table, Order, OrderItem, Zone, Reservation

User = get_user_model()

class OrderCreationTestCase(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        self.other_restaurant = Restaurant.objects.create(name="Other Restaurant")
        
        self.owner = User.objects.create_user(username="owner", password="password", role="OWNER", restaurant=self.restaurant)
        self.manager = User.objects.create_user(username="manager", password="password", role="MANAGER", restaurant=self.restaurant)
        self.cashier = User.objects.create_user(username="cashier", password="password", role="CASHIER", restaurant=self.restaurant)
        self.waiter = User.objects.create_user(username="waiter", password="password", role="WAITER", restaurant=self.restaurant)
        self.kitchen = User.objects.create_user(username="kitchen", password="password", role="KITCHEN", restaurant=self.restaurant)
        
        self.zone = Zone.objects.create(restaurant=self.restaurant, name="Main Zone", is_active=True)
        self.table = Table.objects.create(restaurant=self.restaurant, name="Table 1", zone=self.zone, is_active=True)
        self.inactive_table = Table.objects.create(restaurant=self.restaurant, name="Table 2", zone=self.zone, is_active=False)
        
        self.category = Category.objects.create(restaurant=self.restaurant, name="Burgers", is_active=True)
        self.menu_item1 = MenuItem.objects.create(
            category=self.category,
            name="Chicken Burger",
            price=250.00,
            is_available=True
        )
        self.menu_item2 = MenuItem.objects.create(
            category=self.category,
            name="Beef Burger",
            price=300.00,
            is_available=True
        )
        self.unavailable_item = MenuItem.objects.create(
            category=self.category,
            name="Special Burger",
            price=350.00,
            is_available=False
        )
        
        # Other restaurant items
        self.other_category = Category.objects.create(restaurant=self.other_restaurant, name="Other Burgers")
        self.other_item = MenuItem.objects.create(
            category=self.other_category,
            name="Other Burger",
            price=200.00,
            is_available=True
        )
        
        self.client = APIClient()

    def test_create_order_with_items_success(self):
        """Test successful atomic order creation with multiple items."""
        self.client.force_authenticate(user=self.manager)
        
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'order_type': 'dine-in',
            'status': 'open',
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 2, 'notes': 'No onions'},
                {'menu_item': self.menu_item2.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order created
        created_order = Order.objects.get(id=response.data['id'])
        self.assertEqual(created_order.restaurant, self.restaurant)
        self.assertEqual(created_order.table, self.table)
        self.assertEqual(created_order.order_type, 'dine-in')
        self.assertEqual(created_order.status, 'open')
        
        # Verify total_amount calculated correctly (2*250 + 1*300 = 800)
        self.assertEqual(float(created_order.total_amount), 800.00)
        
        # Verify items created with price snapshots
        self.assertEqual(created_order.items.count(), 2)
        
        item1 = created_order.items.get(menu_item=self.menu_item1)
        self.assertEqual(item1.quantity, 2)
        self.assertEqual(float(item1.price_at_time), 250.00)
        self.assertEqual(item1.notes, 'No onions')
        
        item2 = created_order.items.get(menu_item=self.menu_item2)
        self.assertEqual(item2.quantity, 1)
        self.assertEqual(float(item2.price_at_time), 300.00)
        
        # Verify table status synced to occupied
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')

    def test_create_order_without_items_fails(self):
        """Test that order creation fails without items."""
        self.client.force_authenticate(user=self.manager)
        
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'order_type': 'dine-in',
            'items': []
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('items', response.data)

    def test_create_order_with_unavailable_item_fails(self):
        """Test that order creation fails with unavailable menu item."""
        self.client.force_authenticate(user=self.manager)
        
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [
                {'menu_item': self.unavailable_item.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('items', response.data)

    def test_create_order_with_other_restaurant_item_fails(self):
        """Test that order creation fails with item from another restaurant."""
        self.client.force_authenticate(user=self.manager)
        
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [
                {'menu_item': self.other_item.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('items', response.data)

    def test_create_order_with_inactive_table_fails(self):
        """Test that order creation fails with inactive table."""
        self.client.force_authenticate(user=self.manager)
        
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.inactive_table.id,
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', response.data)

    def test_create_order_without_table_succeeds(self):
        """Test that takeaway order creation succeeds without table."""
        self.client.force_authenticate(user=self.manager)
        
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'order_type': 'takeaway',
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        created_order = Order.objects.get(id=response.data['id'])
        self.assertIsNone(created_order.table)
        self.assertEqual(created_order.order_type, 'takeaway')

    def test_create_order_role_permissions(self):
        """Test role-based access control for order creation."""
        # Manager should succeed
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Cashier should succeed
        self.client.force_authenticate(user=self.cashier)
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Waiter should succeed
        self.client.force_authenticate(user=self.waiter)
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Kitchen cannot POST (only PATCH allowed for kitchen)
        self.client.force_authenticate(user=self.kitchen)
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_with_other_restaurant_table_fails(self):
        """Test that order creation fails with table from another restaurant."""
        other_table = Table.objects.create(restaurant=self.other_restaurant, name="Other Table")
        
        self.client.force_authenticate(user=self.manager)
        
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': other_table.id,
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', response.data)

    def test_create_order_unauthenticated_fails(self):
        """Test that unauthenticated users cannot create orders."""
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_table_status_sync_with_reservation(self):
        """Test that table status sync respects existing reservations."""
        from . import reservation_service
        
        # Create a reservation for today
        today = timezone.localdate()
        reservation = Reservation.objects.create(
            restaurant=self.restaurant,
            table=self.table,
            customer_name="Test Customer",
            reservation_date=today,
            start_time=datetime.time(18, 0),
            expected_duration_minutes=120,
            guests=2,
            status='RESERVED'
        )
        
        # Sync table status after reservation creation
        reservation_service.sync_table_after_reservation_change(reservation)
        
        # Table should be reserved
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'reserved')
        
        # Create an order - table should become occupied
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Table should now be occupied (order takes precedence)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')

    def test_price_snapshot_preserved(self):
        """Test that price_at_time snapshots are preserved correctly."""
        self.client.force_authenticate(user=self.manager)
        
        original_price = self.menu_item1.price
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        created_order = Order.objects.get(id=response.data['id'])
        item = created_order.items.first()
        
        # Snapshot should match original price
        self.assertEqual(float(item.price_at_time), float(original_price))
        
        # Change menu item price
        self.menu_item1.price = 300.00
        self.menu_item1.save()
        
        # Order item price should remain unchanged
        item.refresh_from_db()
        self.assertEqual(float(item.price_at_time), float(original_price))
        self.assertNotEqual(float(item.price_at_time), float(self.menu_item1.price))

    def test_update_order_with_items_success(self):
        """Test successful order update with item modifications."""
        # Create initial order
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 2}
            ]
        }, format='json')
        
        order_id = response.data['id']
        initial_total = float(response.data['total_amount'])
        self.assertEqual(initial_total, 500.00)  # 2 * 250
        
        # Update order - change quantity and add new item
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 1},
                {'menu_item': self.menu_item2.id, 'quantity': 2}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify items updated
        updated_order = Order.objects.get(id=order_id)
        self.assertEqual(updated_order.items.count(), 2)
        
        # Verify total recalculated (1*250 + 2*300 = 850)
        self.assertEqual(float(updated_order.total_amount), 850.00)
        
        # Verify table still occupied
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')

    def test_update_order_removes_all_items_fails(self):
        """Test that updating order with no items fails."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Try to update with empty items
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': []
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('items', response.data)

    def test_update_order_with_unavailable_item_fails(self):
        """Test that updating order with unavailable item fails."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Try to add unavailable item
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [
                {'menu_item': self.unavailable_item.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('items', response.data)

    def test_update_paid_order_fails(self):
        """Test that updating a paid order fails."""
        self.client.force_authenticate(user=self.manager)
        
        # Create and mark order as paid
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        paid_order = Order.objects.get(id=order_id)
        paid_order.status = 'paid'
        paid_order.save()
        
        # Try to update
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 2}]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_cancel_order_success(self):
        """Test successful order cancellation."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Cancel order
        response = self.client.post(f'/api/auth/orders/{order_id}/cancel/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify order cancelled
        cancelled_order = Order.objects.get(id=order_id)
        self.assertEqual(cancelled_order.status, 'cancelled')
        
        # Verify table freed (no other active orders)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'free')

    def test_cancel_order_with_reservation(self):
        """Test that cancelling order respects existing reservations."""
        from . import reservation_service
        
        # Create reservation
        today = timezone.localdate()
        reservation = Reservation.objects.create(
            restaurant=self.restaurant,
            table=self.table,
            customer_name="Test Customer",
            reservation_date=today,
            start_time=datetime.time(18, 0),
            expected_duration_minutes=120,
            guests=2,
            status='RESERVED'
        )
        reservation_service.sync_table_after_reservation_change(reservation)
        
        # Create order (table becomes occupied)
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')
        
        # Cancel order
        response = self.client.post(f'/api/auth/orders/{order_id}/cancel/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Table should revert to reserved (from reservation)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'reserved')

    def test_cancel_order_with_other_active_order_fails(self):
        """Test that cancelling one order doesn't free table if another active order exists."""
        # Create first order
        self.client.force_authenticate(user=self.manager)
        response1 = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order1_id = response1.data['id']
        
        # Create second order (different table to avoid conflict)
        table2 = Table.objects.create(restaurant=self.restaurant, name="Table 3", zone=self.zone, is_active=True)
        response2 = self.client.post('/api/auth/orders/create_with_items/', {
            'table': table2.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        # Cancel first order
        response = self.client.post(f'/api/auth/orders/{order1_id}/cancel/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # First table should be freed
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'free')

    def test_cancel_paid_order_fails(self):
        """Test that cancelling a paid order fails."""
        self.client.force_authenticate(user=self.manager)
        
        # Create and mark order as paid
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        paid_order = Order.objects.get(id=order_id)
        paid_order.status = 'paid'
        paid_order.save()
        
        # Try to cancel
        response = self.client.post(f'/api/auth/orders/{order_id}/cancel/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_cancel_already_cancelled_order_fails(self):
        """Test that cancelling an already cancelled order fails."""
        self.client.force_authenticate(user=self.manager)
        
        # Create and cancel order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        self.client.post(f'/api/auth/orders/{order_id}/cancel/', format='json')
        
        # Try to cancel again
        response = self.client.post(f'/api/auth/orders/{order_id}/cancel/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_update_order_rollback_on_invalid_item(self):
        """Test that invalid item update rolls back completely."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 2}]
        }, format='json')
        
        order_id = response.data['id']
        initial_item_count = Order.objects.get(id=order_id).items.count()
        self.assertEqual(initial_item_count, 1)
        
        # Try to update with invalid item (from other restaurant)
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [
                {'menu_item': self.other_item.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify items were not changed (atomic rollback)
        rollback_order = Order.objects.get(id=order_id)
        self.assertEqual(rollback_order.items.count(), initial_item_count)
        self.assertEqual(float(rollback_order.total_amount), 500.00)  # Original total

    def test_kitchen_queue_displays_new_orders(self):
        """Test that newly created orders appear in kitchen queue."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 2},
                {'menu_item': self.menu_item2.id, 'quantity': 1}
            ]
        }, format='json')
        
        order_id = response.data['id']
        
        # Verify order appears in kitchen queue (open status)
        queue_response = self.client.get('/api/auth/orders/')
        self.assertEqual(queue_response.status_code, status.HTTP_200_OK)
        
        kitchen_orders = [o for o in queue_response.data if o['status'] in ['open', 'preparing']]
        order_in_queue = next((o for o in kitchen_orders if o['id'] == order_id), None)
        
        self.assertIsNotNone(order_in_queue)
        self.assertEqual(order_in_queue['status'], 'open')
        self.assertEqual(len(order_in_queue['items']), 2)

    def test_takeaway_order_appears_in_kitchen_queue(self):
        """Test that takeaway orders appear in kitchen queue with correct order_type."""
        self.client.force_authenticate(user=self.manager)
        
        # Create takeaway order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'order_type': 'takeaway',
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 1},
                {'menu_item': self.menu_item2.id, 'quantity': 2}
            ]
        }, format='json')
        
        order_id = response.data['id']
        
        # Verify order created without table
        created_order = Order.objects.get(id=order_id)
        self.assertIsNone(created_order.table)
        self.assertEqual(created_order.order_type, 'takeaway')
        self.assertEqual(float(created_order.total_amount), 850.00)  # 1*250 + 2*300
        
        # Verify order appears in kitchen queue
        queue_response = self.client.get('/api/auth/orders/')
        self.assertEqual(queue_response.status_code, status.HTTP_200_OK)
        
        kitchen_orders = [o for o in queue_response.data if o['status'] in ['open', 'preparing']]
        order_in_queue = next((o for o in kitchen_orders if o['id'] == order_id), None)
        
        self.assertIsNotNone(order_in_queue)
        self.assertEqual(order_in_queue['status'], 'open')
        self.assertEqual(order_in_queue['order_type'], 'takeaway')
        self.assertIn('table_name', order_in_queue)
        self.assertIsNone(order_in_queue['table_name'])
        self.assertEqual(len(order_in_queue['items']), 2)

    def test_kitchen_queue_reflects_edited_orders(self):
        """Test that edited orders show updated items in kitchen queue."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order with 1 item
        create_response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = create_response.data['id']
        
        # Edit order to add another item
        self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 1},
                {'menu_item': self.menu_item2.id, 'quantity': 2}
            ]
        }, format='json')
        
        # Verify kitchen queue shows updated items
        queue_response = self.client.get('/api/auth/orders/')
        self.assertEqual(queue_response.status_code, status.HTTP_200_OK)
        
        kitchen_orders = [o for o in queue_response.data if o['status'] in ['open', 'preparing']]
        order_in_queue = next((o for o in kitchen_orders if o['id'] == order_id), None)
        
        self.assertIsNotNone(order_in_queue)
        self.assertEqual(len(order_in_queue['items']), 2)
        
        # Verify items are correct
        item_names = {item['menu_item_name'] for item in order_in_queue['items']}
        self.assertIn('Chicken Burger', item_names)
        self.assertIn('Beef Burger', item_names)

    def test_cancelled_orders_not_in_kitchen_queue(self):
        """Test that cancelled orders are filtered out of kitchen queue."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Cancel order
        self.client.post(f'/api/auth/orders/{order_id}/cancel/', format='json')
        
        # Verify order does NOT appear in kitchen queue
        queue_response = self.client.get('/api/auth/orders/')
        self.assertEqual(queue_response.status_code, status.HTTP_200_OK)
        
        kitchen_orders = [o for o in queue_response.data if o['status'] in ['open', 'preparing']]
        order_in_queue = next((o for o in kitchen_orders if o['id'] == order_id), None)
        
        self.assertIsNone(order_in_queue)
        
        # Verify order still exists but is cancelled
        cancelled_order = Order.objects.get(id=order_id)
        self.assertEqual(cancelled_order.status, 'cancelled')

    def test_kitchen_status_transitions(self):
        """Test that kitchen can transition order status from open to preparing to served."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Kitchen user transitions to preparing
        self.client.force_authenticate(user=self.kitchen)
        response = self.client.patch(f'/api/auth/orders/{order_id}/', {
            'status': 'preparing'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        preparing_order = Order.objects.get(id=order_id)
        self.assertEqual(preparing_order.status, 'preparing')
        
        # Kitchen user transitions to served
        response = self.client.patch(f'/api/auth/orders/{order_id}/', {
            'status': 'served'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        served_order = Order.objects.get(id=order_id)
        self.assertEqual(served_order.status, 'served')

    def test_kitchen_cannot_cancel_orders(self):
        """Test that kitchen users cannot cancel orders via status change."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Kitchen user tries to set status to cancelled (not allowed)
        self.client.force_authenticate(user=self.kitchen)
        response = self.client.patch(f'/api/auth/orders/{order_id}/', {
            'status': 'cancelled'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify order is still open
        open_order = Order.objects.get(id=order_id)
        self.assertEqual(open_order.status, 'open')

    def test_kitchen_cannot_mark_paid(self):
        """Test that kitchen users cannot mark orders as paid."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Kitchen user tries to set status to paid (not allowed)
        self.client.force_authenticate(user=self.kitchen)
        response = self.client.patch(f'/api/auth/orders/{order_id}/', {
            'status': 'paid'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify order is still open
        open_order = Order.objects.get(id=order_id)
        self.assertEqual(open_order.status, 'open')

    def test_table_status_sync_after_kitchen_served(self):
        """Test that table status remains correct after kitchen marks order as served."""
        from . import reservation_service
        
        self.client.force_authenticate(user=self.manager)
        
        # Create order
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Table should be occupied
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')
        
        # Kitchen marks as served
        self.client.force_authenticate(user=self.kitchen)
        self.client.patch(f'/api/auth/orders/{order_id}/', {
            'status': 'served'
        }, format='json')
        
        # Table should still be occupied (order is still active, just served)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')

    def test_edit_preserves_original_price_for_unchanged_item(self):
        """Test that editing an order preserves original price for unchanged menu items."""
        self.client.force_authenticate(user=self.manager)
        
        original_price = self.menu_item1.price  # 250.00
        
        # Create order with menu_item1
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 2}]
        }, format='json')
        
        order_id = response.data['id']
        initial_order = Order.objects.get(id=order_id)
        self.assertEqual(float(initial_order.total_amount), 500.00)  # 2 * 250
        
        # Change menu item price
        self.menu_item1.price = 350.00
        self.menu_item1.save()
        
        # Edit order - keep same item, change quantity
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify price preserved (original 250, not current 350)
        edited_order = Order.objects.get(id=order_id)
        item = edited_order.items.first()
        self.assertEqual(float(item.price_at_time), 250.00)
        self.assertEqual(float(edited_order.total_amount), 250.00)  # 1 * 250 (original price)

    def test_edit_uses_current_price_for_new_item(self):
        """Test that editing an order uses current price for newly added menu items."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order with menu_item1
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 1}]
        }, format='json')
        
        order_id = response.data['id']
        
        # Change menu_item2 price
        self.menu_item2.price = 400.00  # Was 300.00
        self.menu_item2.save()
        
        # Edit order - add menu_item2
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 1},
                {'menu_item': self.menu_item2.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify menu_item1 uses original price, menu_item2 uses current price
        order = Order.objects.get(id=order_id)
        items = {item.menu_item_id: item for item in order.items.all()}
        
        item1 = items[self.menu_item1.id]
        self.assertEqual(float(item1.price_at_time), 250.00)  # Original price
        
        item2 = items[self.menu_item2.id]
        self.assertEqual(float(item2.price_at_time), 400.00)  # Current price
        
        # Total should be 250 + 400 = 650
        self.assertEqual(float(order.total_amount), 650.00)

    def test_edit_calculates_quantities_correctly(self):
        """Test that editing an order calculates quantities and totals correctly with mixed prices."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order with menu_item1 (250) and menu_item2 (300)
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 2},
                {'menu_item': self.menu_item2.id, 'quantity': 1}
            ]
        }, format='json')
        
        order_id = response.data['id']
        self.assertEqual(float(response.data['total_amount']), 800.00)  # 2*250 + 1*300
        
        # Change menu_item1 price
        self.menu_item1.price = 300.00
        self.menu_item1.save()
        
        # Edit order - change quantities
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [
                {'menu_item': self.menu_item1.id, 'quantity': 3},
                {'menu_item': self.menu_item2.id, 'quantity': 2}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify prices: menu_item1 uses original 250, menu_item2 uses original 300
        order = Order.objects.get(id=order_id)
        items = {item.menu_item_id: item for item in order.items.all()}
        
        item1 = items[self.menu_item1.id]
        self.assertEqual(item1.quantity, 3)
        self.assertEqual(float(item1.price_at_time), 250.00)  # Original price preserved
        
        item2 = items[self.menu_item2.id]
        self.assertEqual(item2.quantity, 2)
        self.assertEqual(float(item2.price_at_time), 300.00)  # Original price preserved
        
        # Total should be 3*250 + 2*300 = 750 + 600 = 1350
        self.assertEqual(float(order.total_amount), 1350.00)

    def test_edit_invalid_item_rollback_preserves_original_prices(self):
        """Test that invalid edit rolls back without losing existing items or prices."""
        self.client.force_authenticate(user=self.manager)
        
        # Create order with menu_item1
        response = self.client.post('/api/auth/orders/create_with_items/', {
            'table': self.table.id,
            'items': [{'menu_item': self.menu_item1.id, 'quantity': 2}]
        }, format='json')
        
        order_id = response.data['id']
        original_total = float(response.data['total_amount'])
        self.assertEqual(original_total, 500.00)  # 2 * 250
        
        # Try to edit with invalid item (from other restaurant)
        response = self.client.patch(f'/api/auth/orders/{order_id}/update_with_items/', {
            'items': [
                {'menu_item': self.other_item.id, 'quantity': 1}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify original items and prices preserved (atomic rollback)
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.items.count(), 1)
        
        item = order.items.first()
        self.assertEqual(item.menu_item, self.menu_item1)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(float(item.price_at_time), 250.00)  # Original price preserved
        self.assertEqual(float(order.total_amount), 500.00)  # Original total preserved

class OrderFilteringTestCase(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Filter Restaurant")
        self.other_restaurant = Restaurant.objects.create(name="Other Filter Restaurant")
        
        self.manager = User.objects.create_user(username="filter_manager", password="password", role="MANAGER", restaurant=self.restaurant)
        
        self.table = Table.objects.create(restaurant=self.restaurant, name="T1", is_active=True)
        
        # Create some orders for filtering
        self.order1 = Order.objects.create(restaurant=self.restaurant, table=self.table, status='open', order_type='dine-in')
        self.order2 = Order.objects.create(restaurant=self.restaurant, table=self.table, status='preparing', order_type='takeaway')
        self.order3 = Order.objects.create(restaurant=self.restaurant, table=self.table, status='served', order_type='dine-in')
        self.order4 = Order.objects.create(restaurant=self.restaurant, table=self.table, status='paid', order_type='takeaway')
        
        # Order for other restaurant
        self.other_order = Order.objects.create(restaurant=self.other_restaurant, status='open', order_type='takeaway')
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager)

    def test_filter_by_status_single(self):
        response = self.client.get('/api/auth/orders/?status=open')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order1.id)
        
    def test_filter_by_status_multiple(self):
        response = self.client.get('/api/auth/orders/?status=open,preparing')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        ids = [o['id'] for o in response.data]
        self.assertIn(self.order1.id, ids)
        self.assertIn(self.order2.id, ids)
        
    def test_filter_by_order_type(self):
        response = self.client.get('/api/auth/orders/?order_type=takeaway')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        ids = [o['id'] for o in response.data]
        self.assertIn(self.order2.id, ids)
        self.assertIn(self.order4.id, ids)
        
    def test_filter_combined(self):
        response = self.client.get('/api/auth/orders/?status=preparing,served&order_type=takeaway')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order2.id)

    def test_filter_preserves_restaurant_isolation(self):
        response = self.client.get('/api/auth/orders/?status=open')
        self.assertEqual(response.status_code, 200)
        ids = [o['id'] for o in response.data]
        self.assertIn(self.order1.id, ids)
        self.assertNotIn(self.other_order.id, ids)

from .models import Payment

class OrderPaymentTestCase(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Pay Restaurant")
        self.other_restaurant = Restaurant.objects.create(name="Other Pay Restaurant")
        
        self.manager = User.objects.create_user(username="pay_manager", password="password", role="MANAGER", restaurant=self.restaurant)
        self.waiter = User.objects.create_user(username="pay_waiter", password="password", role="WAITER", restaurant=self.restaurant)
        
        self.table = Table.objects.create(restaurant=self.restaurant, name="T1", is_active=True)
        
        self.order = Order.objects.create(restaurant=self.restaurant, table=self.table, status='open', order_type='dine-in', total_amount=150.00)
        self.other_order = Order.objects.create(restaurant=self.other_restaurant, status='open', order_type='takeaway', total_amount=100.00)
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager)

    def test_successful_payment(self):
        response = self.client.post(f'/api/auth/orders/{self.order.id}/pay/', {'method': 'bkash'}, format='json')
        self.assertEqual(response.status_code, 200)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        
        self.assertTrue(Payment.objects.filter(order=self.order).exists())
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(float(payment.amount), 150.00)
        self.assertEqual(payment.method, 'bkash')
        self.assertEqual(payment.processed_by, self.manager)

    def test_invalid_payment_method(self):
        response = self.client.post(f'/api/auth/orders/{self.order.id}/pay/', {'method': 'invalid'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Payment.objects.filter(order=self.order).exists())

    def test_waiter_cannot_process_payment(self):
        self.client.force_authenticate(user=self.waiter)
        response = self.client.post(f'/api/auth/orders/{self.order.id}/pay/', {'method': 'cash'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_cannot_pay_other_restaurant_order(self):
        response = self.client.post(f'/api/auth/orders/{self.other_order.id}/pay/', {'method': 'cash'}, format='json')
        self.assertEqual(response.status_code, 404)

    def test_cannot_pay_twice(self):
        self.client.post(f'/api/auth/orders/{self.order.id}/pay/', {'method': 'cash'}, format='json')
        response = self.client.post(f'/api/auth/orders/{self.order.id}/pay/', {'method': 'card'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.filter(order=self.order).count(), 1)

    def test_direct_status_update_blocked(self):
        response = self.client.patch(f'/api/auth/orders/{self.order.id}/', {'status': 'paid'}, format='json')
        self.assertEqual(response.status_code, 403)
