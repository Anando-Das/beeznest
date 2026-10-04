from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.me_url = reverse('me')
        self.csrf_url = reverse('csrf')

        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'restaurant_name': 'Test Restaurant'
        }

    def test_signup_success(self):
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, 'OWNER')
        self.assertIsNotNone(user.restaurant)
        self.assertEqual(user.restaurant.name, 'Test Restaurant')
        
        # Verify it did NOT automatically log in
        response_me = self.client.get(self.me_url)
        self.assertEqual(response_me.status_code, status.HTTP_403_FORBIDDEN)

    def test_signup_failure_weak_password(self):
        bad_data = self.user_data.copy()
        bad_data['password'] = '123'
        response = self.client.post(self.signup_url, bad_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_signup_duplicate_username(self):
        self.client.post(self.signup_url, self.user_data, format='json')
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1) # Only the first one was created

    def test_signup_missing_restaurant(self):
        bad_data = self.user_data.copy()
        del bad_data['restaurant_name']
        response = self.client.post(self.signup_url, bad_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_login_success(self):
        # Create user via signup view to ensure correct creation logic
        self.client.post(self.signup_url, self.user_data, format='json')
        # We don't need to logout anymore since signup doesn't login
        
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'StrongPassword123!'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify session works
        response_me = self.client.get(self.me_url)
        self.assertEqual(response_me.status_code, status.HTTP_200_OK)
        self.assertEqual(response_me.data['username'], 'testuser')

    def test_login_failure(self):
        self.client.post(self.signup_url, self.user_data, format='json')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        # Create and login
        self.client.post(self.signup_url, self.user_data, format='json')
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'StrongPassword123!'
        }, format='json')
        
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify we can no longer access 'me'
        response_me = self.client.get(self.me_url)
        self.assertEqual(response_me.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_csrf_endpoint(self):
        response = self.client.get(self.csrf_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrfToken', response.data)
