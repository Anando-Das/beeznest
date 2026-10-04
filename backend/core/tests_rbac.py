from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Restaurant, Category, MenuItem, Table, Order, Customer, Expense, DayClose

User = get_user_model()

class RBACAndStaffTests(TestCase):
    def setUp(self):
        self.client_owner1 = APIClient()
        self.client_manager1 = APIClient()
        self.client_waiter1 = APIClient()
        self.client_owner2 = APIClient()
        self.client_unassigned = APIClient()

        # Create restaurants
        self.rest1 = Restaurant.objects.create(name="Rest 1")
        self.rest2 = Restaurant.objects.create(name="Rest 2")

        # Create users
        self.owner1 = User.objects.create_user(username="owner1", password="pw", role="OWNER", restaurant=self.rest1)
        self.manager1 = User.objects.create_user(username="manager1", password="pw", role="MANAGER", restaurant=self.rest1)
        self.waiter1 = User.objects.create_user(username="waiter1", password="pw", role="WAITER", restaurant=self.rest1)
        
        self.owner2 = User.objects.create_user(username="owner2", password="pw", role="OWNER", restaurant=self.rest2)
        
        self.unassigned = User.objects.create_user(username="unassigned", password="pw")

        # Authenticate clients
        self.client_owner1.force_authenticate(user=self.owner1)
        self.client_manager1.force_authenticate(user=self.manager1)
        self.client_waiter1.force_authenticate(user=self.waiter1)
        self.client_owner2.force_authenticate(user=self.owner2)
        self.client_unassigned.force_authenticate(user=self.unassigned)

    def test_owner_staff_creation(self):
        url = reverse('staff-list')
        data = {
            "username": "newstaff",
            "password": "StrongPassword123!",
            "first_name": "New",
            "last_name": "Staff",
            "role": "CASHIER"
        }
        res = self.client_owner1.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username="newstaff")
        self.assertEqual(new_user.restaurant, self.rest1)
        self.assertEqual(new_user.role, "CASHIER")

    def test_owner_can_create_owner(self):
        url = reverse('staff-list')
        data = {
            "username": "newowner",
            "password": "StrongPassword123!",
            "role": "OWNER"
        }
        res = self.client_owner1.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_manager_cannot_assign_owner(self):
        url = reverse('staff-list')
        data = {
            "username": "badstaff",
            "password": "StrongPassword123!",
            "role": "OWNER"
        }
        res = self.client_manager1.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_existing_unassigned(self):
        url = reverse('staff-assign-existing')
        data = {
            "username": "unassigned",
            "role": "KITCHEN"
        }
        res = self.client_owner1.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.unassigned.refresh_from_db()
        self.assertEqual(self.unassigned.restaurant, self.rest1)
        self.assertEqual(self.unassigned.role, "KITCHEN")

    def test_manager_can_create_staff(self):
        url = reverse('staff-list')
        data = {
            "username": "newstaff2",
            "password": "StrongPassword123!",
            "role": "CASHIER"
        }
        res = self.client_manager1.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_unassigned_user_restrictions(self):
        url = reverse('category-list')
        res = self.client_unassigned.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_waiter_cannot_access_expenses(self):
        url = reverse('expense-list')
        res = self.client_waiter1.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_access_expenses(self):
        url = reverse('expense-list')
        res = self.client_manager1.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_cross_restaurant_isolation(self):
        # Owner 1 creates a category
        url = reverse('category-list')
        self.client_owner1.post(url, {"name": "Cat1"}, format='json')
        
        # Owner 2 should not see it
        res = self.client_owner2.get(url)
        self.assertEqual(len(res.data), 0)

    def test_edit_staff_role(self):
        url = reverse('staff-list')
        self.client_owner1.post(url, {
            "username": "toupdate",
            "password": "StrongPassword123!",
            "role": "WAITER"
        }, format='json')
        user = User.objects.get(username="toupdate")
        
        detail_url = reverse('staff-detail', args=[user.id])
        res = self.client_owner1.patch(detail_url, {"role": "MANAGER"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.role, "MANAGER")
        
        # Owner can escalate to OWNER
        res2 = self.client_owner1.patch(detail_url, {"role": "OWNER"}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.role, "OWNER")
        
        # Manager cannot escalate to OWNER
        res3 = self.client_manager1.patch(detail_url, {"role": "OWNER"}, format='json')
        self.assertEqual(res3.status_code, status.HTTP_403_FORBIDDEN)

    def test_deactivate_staff_access(self):
        url = reverse('staff-list')
        self.client_owner1.post(url, {
            "username": "deact",
            "password": "StrongPassword123!",
            "role": "MANAGER"
        }, format='json')
        user = User.objects.get(username="deact")
        
        staff_client = APIClient()
        staff_client.force_authenticate(user=user)
        
        # Verify access initially
        cat_url = reverse('category-list')
        resp = staff_client.get(cat_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        # Owner deactivates staff
        detail_url = reverse('staff-detail', args=[user.id])
        self.client_owner1.patch(detail_url, {"is_active": False}, format='json')
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        
        # Verify staff access is now forbidden
        resp2 = staff_client.get(cat_url)
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_staff_not_allowed(self):
        url = reverse('staff-list')
        self.client_owner1.post(url, {
            "username": "todelete",
            "password": "StrongPassword123!",
            "role": "WAITER"
        }, format='json')
        user = User.objects.get(username="todelete")
        
        detail_url = reverse('staff-detail', args=[user.id])
        response = self.client_owner1.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
