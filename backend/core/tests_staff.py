from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import Restaurant

User = get_user_model()

class StaffTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.restaurant = Restaurant.objects.create(name='Test Rest', address='123')
        
        self.owner = User.objects.create_user(
            username='owner', password='password123!', role='OWNER', restaurant=self.restaurant
        )
        
        self.staff = User.objects.create_user(
            username='staff', password='password123!', role='WAITER', restaurant=self.restaurant, is_active=True
        )
        
        self.unauth_user = User.objects.create_user(
            username='hacker', password='password123!', role='WAITER', restaurant=self.restaurant
        )

        self.staff_url = f'/api/auth/staff/{self.staff.id}/'
        
    def test_deactivate_staff(self):
        self.client.force_authenticate(user=self.owner)
        
        # Deactivate
        response = self.client.patch(self.staff_url, {'is_active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.staff.refresh_from_db()
        self.assertFalse(self.staff.is_active)
        
        # Reactivate
        response = self.client.patch(self.staff_url, {'is_active': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)

    def test_unauthorized_deactivate(self):
        self.client.force_authenticate(user=self.unauth_user)
        response = self.client.patch(self.staff_url, {'is_active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)
