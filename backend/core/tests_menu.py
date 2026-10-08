from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Restaurant, Category, MenuItem, MenuItemPriceHistory, Table, Order, OrderItem

User = get_user_model()

class MenuManagementTestCase(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        
        self.owner = User.objects.create_user(username="owner", password="password", role="OWNER", restaurant=self.restaurant)
        self.manager = User.objects.create_user(username="manager", password="password", role="MANAGER", restaurant=self.restaurant)
        self.kitchen = User.objects.create_user(username="kitchen", password="password", role="KITCHEN", restaurant=self.restaurant)
        self.cashier = User.objects.create_user(username="cashier", password="password", role="CASHIER", restaurant=self.restaurant)
        self.waiter = User.objects.create_user(username="waiter", password="password", role="WAITER", restaurant=self.restaurant)
        
        self.client = APIClient()

        self.category = Category.objects.create(restaurant=self.restaurant, name="Burgers", is_active=True)
        self.menu_item = MenuItem.objects.create(
            category=self.category,
            name="Chicken Burger",
            price=250.00,
            is_available=True
        )
        self.table = Table.objects.create(restaurant=self.restaurant, name="Table 1")

    def test_category_permissions(self):
        # Owner can create
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/auth/categories/', {'name': 'Pizza', 'sort_order': 1})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Manager can create
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/auth/categories/', {'name': 'Drinks', 'sort_order': 2})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Cashier cannot create
        self.client.force_authenticate(user=self.cashier)
        response = self.client.post('/api/auth/categories/', {'name': 'Desserts', 'sort_order': 3})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Kitchen cannot create
        self.client.force_authenticate(user=self.kitchen)
        response = self.client.post('/api/auth/categories/', {'name': 'Desserts', 'sort_order': 3})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_menu_item_create_edit_delete_permissions(self):
        # Manager can create
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/auth/menu-items/', {
            'category': self.category.id,
            'name': 'Beef Burger',
            'price': 300.00
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_item_id = response.data['id']
        
        # Owner can edit
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(f'/api/auth/menu-items/{new_item_id}/', {'name': 'Double Beef Burger'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cashier cannot edit
        self.client.force_authenticate(user=self.cashier)
        response = self.client.patch(f'/api/auth/menu-items/{new_item_id}/', {'name': 'Hacked Burger'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Manager can delete
        self.client.force_authenticate(user=self.manager)
        response = self.client.delete(f'/api/auth/menu-items/{new_item_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_menu_item_price_permissions(self):
        # Cashier cannot change price
        self.client.force_authenticate(user=self.cashier)
        response = self.client.patch(f'/api/auth/menu-items/{self.menu_item.id}/', {'price': 10.00})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Kitchen cannot change price
        self.client.force_authenticate(user=self.kitchen)
        response = self.client.patch(f'/api/auth/menu-items/{self.menu_item.id}/', {'price': 10.00})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Owner can change price
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(f'/api/auth/menu-items/{self.menu_item.id}/', {'price': 280.00})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Price history should be created
        history = MenuItemPriceHistory.objects.filter(menu_item=self.menu_item).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.old_price, 250.00)
        self.assertEqual(history.new_price, 280.00)
        self.assertEqual(history.changed_by, self.owner)

    def test_menu_item_availability_permissions(self):
        # Kitchen CAN change availability
        self.client.force_authenticate(user=self.kitchen)
        response = self.client.patch(f'/api/auth/menu-items/{self.menu_item.id}/', {'is_available': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.menu_item.refresh_from_db()
        self.assertFalse(self.menu_item.is_available)
        
        # Cashier cannot change availability
        self.client.force_authenticate(user=self.cashier)
        response = self.client.patch(f'/api/auth/menu-items/{self.menu_item.id}/', {'is_available': True})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Owner can change availability
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(f'/api/auth/menu-items/{self.menu_item.id}/', {'is_available': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_protection(self):
        # Create an order with the item at price 250
        order = Order.objects.create(restaurant=self.restaurant, table=self.table)
        order_item = OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=1,
            price_at_time=250.00
        )
        
        # Change price of the item
        self.client.force_authenticate(user=self.owner)
        self.client.patch(f'/api/auth/menu-items/{self.menu_item.id}/', {'price': 300.00})
        
        # Verify old order price remains 250
        order_item.refresh_from_db()
        self.assertEqual(order_item.price_at_time, 250.00)
        
        # Deactivate item
        self.client.patch(f'/api/auth/menu-items/{self.menu_item.id}/', {'is_available': False})
        
        # Attempt to order inactive item
        self.client.force_authenticate(user=self.cashier)
        order2 = Order.objects.create(restaurant=self.restaurant, table=self.table)
        response = self.client.post('/api/auth/order-items/', {
            'order': order2.id,
            'menu_item': self.menu_item.id,
            'quantity': 1
        })
        # Should be rejected because it's inactive
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('menu_item', response.data)
