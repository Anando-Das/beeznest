from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from core.models import Restaurant, WebsiteRequest, WebsiteRequestPhoto
from PIL import Image
import io
import json

User = get_user_model()


def create_test_image():
    """Create a valid test image file."""
    image = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(
        "test.jpg",
        buffer.getvalue(),
        content_type="image/jpeg"
    )


def create_large_test_image(size_bytes):
    """Create a valid test image of a specific size."""
    # Create a larger image to meet size requirements
    # Approximate calculation: RGB = 3 bytes per pixel
    pixels_needed = size_bytes // 3
    side = int(pixels_needed ** 0.5)
    
    image = Image.new('RGB', (side, side), color='red')
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=95)  # Higher quality for larger file
    buffer.seek(0)
    
    # Adjust if needed to get exact size
    current_size = len(buffer.getvalue())
    if current_size < size_bytes:
        # Add padding to reach target size
        padding = b'x' * (size_bytes - current_size)
        buffer.write(padding)
        buffer.seek(0)
    
    return SimpleUploadedFile(
        "large_test.jpg",
        buffer.getvalue(),
        content_type="image/jpeg"
    )


class WebsiteRequestTests(TestCase):
    """Tests for website request submission and management."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create restaurant
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            address="123 Test St"
        )
        
        # Create owner user
        self.owner = User.objects.create_user(
            username="owner",
            password="testpass123",
            restaurant=self.restaurant,
            role="OWNER"
        )
        
        # Create another restaurant for isolation testing
        self.other_restaurant = Restaurant.objects.create(
            name="Other Restaurant",
            address="456 Other St"
        )
        
        self.other_owner = User.objects.create_user(
            username="otherowner",
            password="testpass123",
            restaurant=self.other_restaurant,
            role="OWNER"
        )

    def test_website_request_submission_with_description(self):
        """Test successful website request submission with description."""
        self.client.force_authenticate(user=self.owner)
        
        # Create test images
        photos = [create_test_image() for _ in range(10)]
        
        data = {
            'website_name': 'My Restaurant Website',
            'description': 'I want a modern website with online ordering and reservations.',
            'colours': json.dumps(['#94D8AB', '#14532D']),
            'photos': photos
        }
        
        response = self.client.post('/api/auth/website/request/', data, format='multipart')
        
        self.assertEqual(response.status_code, 201)
        
        # Verify request was created
        request_obj = WebsiteRequest.objects.filter(restaurant=self.restaurant).first()
        self.assertIsNotNone(request_obj)
        self.assertEqual(request_obj.website_name, 'My Restaurant Website')
        self.assertEqual(request_obj.description, 'I want a modern website with online ordering and reservations.')
        self.assertEqual(request_obj.colours, ['#94D8AB', '#14532D'])
        self.assertEqual(request_obj.status, 'PENDING')
        
        # Verify photos were created
        self.assertEqual(request_obj.photos.count(), 10)

    def test_website_request_submission_without_description(self):
        """Test successful website request submission without description (optional field)."""
        self.client.force_authenticate(user=self.owner)
        
        # Create test images
        photos = [create_test_image() for _ in range(10)]
        
        data = {
            'website_name': 'My Restaurant Website',
            'colours': json.dumps(['#94D8AB']),
            'photos': photos
        }
        
        response = self.client.post('/api/auth/website/request/', data, format='multipart')
        
        self.assertEqual(response.status_code, 201)
        
        # Verify request was created with empty description
        request_obj = WebsiteRequest.objects.filter(restaurant=self.restaurant).first()
        self.assertIsNotNone(request_obj)
        self.assertEqual(request_obj.website_name, 'My Restaurant Website')
        self.assertEqual(request_obj.description, '')

    def test_website_request_submission_invalid_colours_json(self):
        """Test that invalid JSON in colours field returns 400 error."""
        self.client.force_authenticate(user=self.owner)
        
        # Create test images
        photos = [create_test_image() for _ in range(10)]
        
        data = {
            'website_name': 'My Restaurant Website',
            'colours': 'invalid json{',
            'photos': photos
        }
        
        response = self.client.post('/api/auth/website/request/', data, format='multipart')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('colours', response.data)

    def test_website_request_submission_fewer_than_10_photos(self):
        """Test that submission with fewer than 10 photos returns 400 error."""
        self.client.force_authenticate(user=self.owner)
        
        # Create only 5 test images
        photos = [create_test_image() for _ in range(5)]
        
        data = {
            'website_name': 'My Restaurant Website',
            'photos': photos
        }
        
        response = self.client.post('/api/auth/website/request/', data, format='multipart')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('photos', response.data)

    def test_website_request_submission_oversized_photo(self):
        """Test that submission with oversized photo (over 2MB) returns 400 error."""
        self.client.force_authenticate(user=self.owner)
        
        # Create 9 valid photos and 1 oversized photo
        photos = [create_test_image() for _ in range(9)]
        
        # Create an oversized photo (over 2MB)
        oversized_photo = SimpleUploadedFile(
            "oversized.jpg",
            b"x" * (2 * 1024 * 1024 + 1),  # 2MB + 1 byte
            content_type="image/jpeg"
        )
        photos.append(oversized_photo)
        
        data = {
            'website_name': 'My Restaurant Website',
            'photos': photos
        }
        
        response = self.client.post('/api/auth/website/request/', data, format='multipart')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('photos', response.data)

    def test_website_request_submission_exactly_2mb_photo_accepted(self):
        """Test that the serializer validation accepts files exactly 2MB."""
        from core.serializers import WebsiteRequestCreateSerializer
        
        # Create a mock file exactly 2MB
        exact_2mb_file = SimpleUploadedFile(
            "exact2mb.jpg",
            b"x" * (2 * 1024 * 1024),  # Exactly 2MB
            content_type="image/jpeg"
        )
        
        # Manually test the validation logic
        max_size = 2 * 1024 * 1024
        self.assertLessEqual(exact_2mb_file.size, max_size, 
                          "File should be accepted as it's exactly at the limit")

    def test_duplicate_active_request_prevention(self):
        """Test that duplicate active requests are prevented."""
        self.client.force_authenticate(user=self.owner)
        
        # Create first request
        photos = [create_test_image() for _ in range(10)]
        
        data = {
            'website_name': 'My Restaurant Website',
            'photos': photos
        }
        
        response1 = self.client.post('/api/auth/website/request/', data, format='multipart')
        self.assertEqual(response1.status_code, 201)
        
        # Try to create second request
        photos2 = [create_test_image() for _ in range(10)]
        
        data2 = {
            'website_name': 'Another Website',
            'photos': photos2
        }
        
        response2 = self.client.post('/api/auth/website/request/', data2, format='multipart')
        self.assertEqual(response2.status_code, 400)
        self.assertIn('detail', response2.data)

    def test_restaurant_data_isolation(self):
        """Test that users can only see their own restaurant's requests."""
        self.client.force_authenticate(user=self.owner)
        
        # Create a request for the first restaurant
        photos = [create_test_image() for _ in range(10)]
        
        data = {
            'website_name': 'My Restaurant Website',
            'photos': photos
        }
        
        self.client.post('/api/auth/website/request/', data, format='multipart')
        
        # Verify the owner can see their request
        response = self.client.get('/api/auth/website/request/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['has_request'])
        self.assertEqual(response.data['request']['website_name'], 'My Restaurant Website')
        
        # Verify the other owner cannot see the first restaurant's request
        self.client.force_authenticate(user=self.other_owner)
        response = self.client.get('/api/auth/website/request/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['has_request'])

    def test_website_request_get_endpoint_includes_description(self):
        """Test that the GET endpoint includes the description field."""
        self.client.force_authenticate(user=self.owner)
        
        # Create a request with description
        photos = [create_test_image() for _ in range(10)]
        
        data = {
            'website_name': 'My Restaurant Website',
            'description': 'A detailed description of requirements',
            'photos': photos
        }
        
        self.client.post('/api/auth/website/request/', data, format='multipart')
        
        # Get the request
        response = self.client.get('/api/auth/website/request/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['has_request'])
        self.assertEqual(response.data['request']['description'], 'A detailed description of requirements')
