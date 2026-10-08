from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Restaurant, Zone, Table, LayoutObject

User = get_user_model()

class LayoutTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant")
        
        self.owner = User.objects.create_user(username='owner', password='password123', restaurant=self.restaurant, role='OWNER')
        self.manager = User.objects.create_user(username='manager', password='password123', restaurant=self.restaurant, role='MANAGER')
        self.waiter = User.objects.create_user(username='waiter', password='password123', restaurant=self.restaurant, role='WAITER')
        self.cashier = User.objects.create_user(username='cashier', password='password123', restaurant=self.restaurant, role='CASHIER')
        self.kitchen = User.objects.create_user(username='kitchen', password='password123', restaurant=self.restaurant, role='KITCHEN')
        
        self.zone1 = Zone.objects.create(restaurant=self.restaurant, name="Zone 1", is_active=True)
        self.zone2 = Zone.objects.create(restaurant=self.restaurant, name="Zone 2", is_active=False)
        self.table1 = Table.objects.create(restaurant=self.restaurant, name="T1", seats=4, shape="RECTANGLE", zone=self.zone1, is_active=True)
        
        self.zones_url = reverse('zone-list')
        self.tables_url = reverse('table-list')
        try:
            self.layout_objects_url = reverse('layoutobject-list')
        except:
            self.layout_objects_url = '/api/auth/layout-objects/'
        
    def get_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    # ZONE TESTS
    def test_zone_crud_owner(self):
        client = self.get_client(self.owner)
        
        # Create
        res = client.post(self.zones_url, {'name': 'New Zone', 'is_active': True})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        zone_id = res.data['id']
        
        # Edit & Deactivate
        url = reverse('zone-detail', args=[zone_id])
        res = client.patch(url, {'name': 'Updated Zone', 'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Updated Zone')
        self.assertFalse(res.data['is_active'])

        # Activate
        res = client.patch(url, {'is_active': True})
        self.assertTrue(res.data['is_active'])

    def test_zone_crud_waiter_forbidden(self):
        client = self.get_client(self.waiter)
        # Create
        res = client.post(self.zones_url, {'name': 'Waiters Zone'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # Edit
        url = reverse('zone-detail', args=[self.zone1.id])
        res = client.patch(url, {'name': 'Hacked'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # TABLE TESTS
    def test_table_crud_owner(self):
        client = self.get_client(self.owner)
        
        # Create
        res = client.post(self.tables_url, {
            'name': 'T2',
            'seats': 6,
            'shape': 'CIRCLE',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        table_id = res.data['id']
        
        # Edit
        url = reverse('table-detail', args=[table_id])
        res = client.patch(url, {
            'name': 'T2-RENAMED',
            'seats': 8,
            'shape': 'SQUARE'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'T2-RENAMED')
        self.assertEqual(res.data['seats'], 8)
        self.assertEqual(res.data['shape'], 'SQUARE')

        # Deactivate
        res = client.patch(url, {'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_active'])

        # Reactivate
        res = client.patch(url, {'is_active': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_active'])

    def test_table_invalid_zone(self):
        client = self.get_client(self.owner)
        # Cannot assign to inactive zone
        res = client.post(self.tables_url, {
            'name': 'T3',
            'seats': 2,
            'shape': 'RECTANGLE',
            'zone': self.zone2.id
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('zone', res.data)

    def test_table_invalid_capacity(self):
        client = self.get_client(self.owner)
        res = client.post(self.tables_url, {
            'name': 'T4',
            'seats': 0,
            'shape': 'RECTANGLE',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('seats', res.data)

    def test_table_duplicate_name(self):
        client = self.get_client(self.owner)
        res = client.post(self.tables_url, {
            'name': 'T1',
            'seats': 4,
            'shape': 'RECTANGLE',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res.data)

    # LAYOUT TESTS
    def test_layout_position_update(self):
        client = self.get_client(self.owner)
        url = reverse('table-detail', args=[self.table1.id])
        res = client.patch(url, {'position_x': 100.5, 'position_y': 200.75})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['position_x'], 100.5)
        self.assertEqual(res.data['position_y'], 200.75)
        
        # Verify persistence
        res2 = client.get(url)
        self.assertEqual(res2.data['position_x'], 100.5)

    def test_table_rbac(self):
        # Manager can write
        client_mgr = self.get_client(self.manager)
        res = client_mgr.post(self.tables_url, {'name': 'MGR-T1', 'seats': 2, 'zone': self.zone1.id})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Waiter cannot write
        client_waiter = self.get_client(self.waiter)
        res = client_waiter.post(self.tables_url, {'name': 'W-T1', 'seats': 2, 'zone': self.zone1.id})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        # Cashier cannot write
        client_cashier = self.get_client(self.cashier)
        res = client_cashier.patch(reverse('table-detail', args=[self.table1.id]), {'name': 'C-T1'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        # Kitchen cannot write
        client_kitchen = self.get_client(self.kitchen)
        res = client_kitchen.patch(reverse('table-detail', args=[self.table1.id]), {'name': 'K-T1'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # LAYOUT OBJECT TESTS
    def test_layout_object_owner_create_cash_counter(self):
        client = self.get_client(self.owner)
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Main Cash Counter',
            'zone': self.zone1.id,
            'position_x': 50,
            'position_y': 50
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['object_type'], 'CASH_COUNTER')
        self.assertEqual(res.data['name'], 'Main Cash Counter')

    def test_layout_object_owner_create_window(self):
        client = self.get_client(self.owner)
        res = client.post(self.layout_objects_url, {
            'object_type': 'WINDOW',
            'name': 'Window 1',
            'zone': self.zone1.id,
            'position_x': 100,
            'position_y': 100
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['object_type'], 'WINDOW')

    def test_layout_object_manager_create(self):
        client = self.get_client(self.manager)
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Manager Counter',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_layout_object_owner_edit(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='Old Name'
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'name': 'New Name'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'New Name')

    def test_layout_object_manager_edit(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window A'
        )
        client = self.get_client(self.manager)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'name': 'Window B'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_layout_object_owner_change_position(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='Counter 1',
            position_x=0,
            position_y=0
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'position_x': 150.5, 'position_y': 250.75})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['position_x'], 150.5)
        self.assertEqual(res.data['position_y'], 250.75)

    def test_layout_object_manager_change_position(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1',
            position_x=0,
            position_y=0
        )
        client = self.get_client(self.manager)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'position_x': 200, 'position_y': 300})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_layout_object_owner_activate_deactivate(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='Counter 1',
            is_active=True
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'

        # Deactivate
        res = client.patch(url, {'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_active'])

        # Reactivate
        res = client.patch(url, {'is_active': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_active'])

    def test_layout_object_manager_activate_deactivate(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1',
            is_active=True
        )
        client = self.get_client(self.manager)
        url = self.layout_objects_url + str(obj.id) + '/'

        # Deactivate
        res = client.patch(url, {'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_active'])

        # Reactivate
        res = client.patch(url, {'is_active': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_active'])

    def test_layout_object_waiter_write_forbidden(self):
        client = self.get_client(self.waiter)
        # Create attempt
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Waiter Counter',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Edit attempt
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1'
        )
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'name': 'Hacked'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_layout_object_cashier_write_forbidden(self):
        client = self.get_client(self.cashier)
        # Create attempt
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Cashier Counter',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Edit attempt
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1'
        )
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'name': 'Hacked'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_layout_object_restaurant_isolation(self):
        # Create another restaurant
        other_restaurant = Restaurant.objects.create(name="Other Restaurant")
        other_owner = User.objects.create_user(
            username='other_owner',
            password='password123',
            restaurant=other_restaurant,
            role='OWNER'
        )
        other_zone = Zone.objects.create(restaurant=other_restaurant, name="Other Zone")

        # Create object in first restaurant
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='My Counter'
        )

        # Other owner cannot see this object
        other_client = self.get_client(other_owner)
        res = other_client.get(self.layout_objects_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)  # Should not see object from other restaurant

        # Other owner can create their own
        res = other_client.post(self.layout_objects_url, {
            'object_type': 'WINDOW',
            'name': 'Other Window',
            'zone': other_zone.id
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_layout_object_zone_relationship(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='Counter 1'
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['zone'], self.zone1.id)
        self.assertEqual(res.data['zone_name'], self.zone1.name)

    def test_layout_object_position_persists(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1',
            position_x=50.5,
            position_y=100.75
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'

        # Read position
        res = client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['position_x'], 50.5)
        self.assertEqual(res.data['position_y'], 100.75)

        # Update position
        res = client.patch(url, {'position_x': 200, 'position_y': 300})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify persistence
        res2 = client.get(url)
        self.assertEqual(res2.data['position_x'], 200)
        self.assertEqual(res2.data['position_y'], 300)

    def test_layout_object_invalid_zone(self):
        client = self.get_client(self.owner)
        # Cannot assign to inactive zone
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Counter',
            'zone': self.zone2.id
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('zone', res.data)

    def test_layout_object_owner_create_window(self):
        client = self.get_client(self.owner)
        res = client.post(self.layout_objects_url, {
            'object_type': 'WINDOW',
            'name': 'Window 1',
            'zone': self.zone1.id,
            'position_x': 100,
            'position_y': 100
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['object_type'], 'WINDOW')

    def test_layout_object_manager_create(self):
        client = self.get_client(self.manager)
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Manager Counter',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_layout_object_owner_edit(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='Old Name'
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'name': 'New Name'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'New Name')

    def test_layout_object_manager_edit(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window A'
        )
        client = self.get_client(self.manager)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'name': 'Window B'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_layout_object_owner_change_position(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='Counter 1',
            position_x=0,
            position_y=0
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'position_x': 150.5, 'position_y': 250.75})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['position_x'], 150.5)
        self.assertEqual(res.data['position_y'], 250.75)

    def test_layout_object_manager_change_position(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1',
            position_x=0,
            position_y=0
        )
        client = self.get_client(self.manager)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'position_x': 200, 'position_y': 300})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_layout_object_owner_activate_deactivate(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='Counter 1',
            is_active=True
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'

        # Deactivate
        res = client.patch(url, {'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_active'])

        # Reactivate
        res = client.patch(url, {'is_active': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_active'])

    def test_layout_object_manager_activate_deactivate(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1',
            is_active=True
        )
        client = self.get_client(self.manager)
        url = self.layout_objects_url + str(obj.id) + '/'

        # Deactivate
        res = client.patch(url, {'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_active'])

        # Reactivate
        res = client.patch(url, {'is_active': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_active'])

    def test_layout_object_waiter_write_forbidden(self):
        client = self.get_client(self.waiter)
        # Create attempt
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Waiter Counter',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Edit attempt
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1'
        )
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'name': 'Hacked'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_layout_object_cashier_write_forbidden(self):
        client = self.get_client(self.cashier)
        # Create attempt
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Cashier Counter',
            'zone': self.zone1.id
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Edit attempt
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1'
        )
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.patch(url, {'name': 'Hacked'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_layout_object_restaurant_isolation(self):
        # Create another restaurant
        other_restaurant = Restaurant.objects.create(name="Other Restaurant")
        other_owner = User.objects.create_user(
            username='other_owner',
            password='password123',
            restaurant=other_restaurant,
            role='OWNER'
        )
        other_zone = Zone.objects.create(restaurant=other_restaurant, name="Other Zone")

        # Create object in first restaurant
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='My Counter'
        )

        # Other owner cannot see this object
        other_client = self.get_client(other_owner)
        res = other_client.get(self.layout_objects_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)  # Should not see object from other restaurant

        # Other owner can create their own
        res = other_client.post(self.layout_objects_url, {
            'object_type': 'WINDOW',
            'name': 'Other Window',
            'zone': other_zone.id
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_layout_object_zone_relationship(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='CASH_COUNTER',
            name='Counter 1'
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'
        res = client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['zone'], self.zone1.id)
        self.assertEqual(res.data['zone_name'], self.zone1.name)

    def test_layout_object_position_persists(self):
        obj = LayoutObject.objects.create(
            restaurant=self.restaurant,
            zone=self.zone1,
            object_type='WINDOW',
            name='Window 1',
            position_x=50.5,
            position_y=100.75
        )
        client = self.get_client(self.owner)
        url = self.layout_objects_url + str(obj.id) + '/'

        # Read position
        res = client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['position_x'], 50.5)
        self.assertEqual(res.data['position_y'], 100.75)

        # Update position
        res = client.patch(url, {'position_x': 200, 'position_y': 300})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify persistence
        res2 = client.get(url)
        self.assertEqual(res2.data['position_x'], 200)
        self.assertEqual(res2.data['position_y'], 300)

    def test_layout_object_invalid_zone(self):
        client = self.get_client(self.owner)
        # Cannot assign to inactive zone
        res = client.post(self.layout_objects_url, {
            'object_type': 'CASH_COUNTER',
            'name': 'Counter',
            'zone': self.zone2.id
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('zone', res.data)
