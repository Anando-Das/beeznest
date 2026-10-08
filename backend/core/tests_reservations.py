import datetime

from django.urls import reverse
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import Restaurant, Table, Zone, Reservation, ReservationHistory, Order

User = get_user_model()


class ReservationManagementTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Beeznest Test")
        self.other_restaurant = Restaurant.objects.create(name="Other Place")

        self.owner = User.objects.create_user(username='owner', password='password123', restaurant=self.restaurant, role='OWNER')
        self.manager = User.objects.create_user(username='manager', password='password123', restaurant=self.restaurant, role='MANAGER')
        self.waiter = User.objects.create_user(username='waiter', password='password123', restaurant=self.restaurant, role='WAITER')
        self.cashier = User.objects.create_user(username='cashier', password='password123', restaurant=self.restaurant, role='CASHIER')
        self.kitchen = User.objects.create_user(username='kitchen', password='password123', restaurant=self.restaurant, role='KITCHEN')
        self.other_owner = User.objects.create_user(username='otherowner', password='password123', restaurant=self.other_restaurant, role='OWNER')

        self.zone = Zone.objects.create(restaurant=self.restaurant, name="Main")
        self.table1 = Table.objects.create(restaurant=self.restaurant, name="T1", seats=4, zone=self.zone, is_active=True)
        self.table2 = Table.objects.create(restaurant=self.restaurant, name="T2", seats=2, zone=self.zone, is_active=True)
        self.inactive = Table.objects.create(restaurant=self.restaurant, name="T-OFF", seats=6, zone=self.zone, is_active=False)
        self.foreign_table = Table.objects.create(restaurant=self.other_restaurant, name="X1", seats=4, is_active=True)

        self.today = timezone.localdate()
        self.list_url = reverse('reservation-list')

    def client_for(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def payload(self, **overrides):
        data = {
            'customer_name': 'Amina',
            'customer_contact': '01700000000',
            'table': self.table1.id,
            'reservation_date': str(self.today),
            'start_time': '19:00:00',
            'expected_duration_minutes': 90,
            'guest_count': 2,
            'notes': 'Window seat',
        }
        data.update(overrides)
        return data

    def create_via_api(self, user=None, **overrides):
        client = self.client_for(user or self.owner)
        res = client.post(self.list_url, self.payload(**overrides), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        return res

    def test_valid_reservation_creation(self):
        res = self.create_via_api()
        self.assertEqual(res.data['status'], 'RESERVED')
        self.assertEqual(res.data['guest_count'], 2)
        self.assertEqual(res.data['table'], self.table1.id)
        self.assertEqual(res.data['created_by'], self.owner.id)
        self.assertEqual(res.data['end_time'], '20:30:00')
        self.assertTrue(ReservationHistory.objects.filter(reservation_id=res.data['id'], action='CREATED').exists())
        self.table1.refresh_from_db()
        self.assertEqual(self.table1.status, 'reserved')

    def test_required_fields(self):
        client = self.client_for(self.owner)
        res = client.post(self.list_url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer_name', res.data)
        self.assertIn('table', res.data)
        self.assertIn('reservation_date', res.data)
        self.assertIn('start_time', res.data)
        self.assertIn('guest_count', res.data)

    def test_positive_guest_count(self):
        client = self.client_for(self.owner)
        res = client.post(self.list_url, self.payload(guest_count=0), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guest_count', res.data)

    def test_positive_duration(self):
        client = self.client_for(self.owner)
        res = client.post(self.list_url, self.payload(expected_duration_minutes=0), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expected_duration_minutes', res.data)

    def test_past_date_rejected(self):
        client = self.client_for(self.owner)
        past = self.today - datetime.timedelta(days=1)
        res = client.post(self.list_url, self.payload(reservation_date=str(past)), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reservation_date', res.data)

    def test_beyond_30_days_rejected(self):
        client = self.client_for(self.owner)
        far = self.today + datetime.timedelta(days=31)
        res = client.post(self.list_url, self.payload(reservation_date=str(far)), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reservation_date', res.data)

    def test_day_30_allowed(self):
        edge = self.today + datetime.timedelta(days=30)
        self.create_via_api(reservation_date=str(edge), start_time='12:00:00')

    def test_inactive_table_rejected(self):
        client = self.client_for(self.owner)
        res = client.post(self.list_url, self.payload(table=self.inactive.id), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', res.data)

    def test_invalid_table_rejected(self):
        client = self.client_for(self.owner)
        res = client.post(self.list_url, self.payload(table=99999), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', res.data)

    def test_foreign_table_rejected(self):
        client = self.client_for(self.owner)
        res = client.post(self.list_url, self.payload(table=self.foreign_table.id), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', res.data)

    def test_guest_count_above_capacity_requires_confirmation(self):
        client = self.client_for(self.owner)
        res = client.post(self.list_url, self.payload(guest_count=8), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guest_count', res.data)
        self.assertIn('requires_capacity_confirmation', res.data)
        confirmed = client.post(self.list_url, self.payload(guest_count=8, confirm_over_capacity=True), format='json')
        self.assertEqual(confirmed.status_code, status.HTTP_201_CREATED, confirmed.data)
        self.assertEqual(confirmed.data['guest_count'], 8)

    def test_overlap_rejected_same_table(self):
        self.create_via_api(start_time='19:00:00', expected_duration_minutes=90)
        client = self.client_for(self.owner)
        res = client.post(self.list_url, self.payload(
            customer_name='Second', start_time='20:00:00', expected_duration_minutes=60
        ), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', res.data)

    def test_different_tables_same_time_allowed(self):
        self.create_via_api(start_time='19:00:00')
        self.create_via_api(customer_name='Other', table=self.table2.id, start_time='19:00:00')

    def test_adjacent_intervals_allowed(self):
        self.create_via_api(start_time='19:00:00', expected_duration_minutes=90)
        self.create_via_api(customer_name='Next', start_time='20:30:00', expected_duration_minutes=60)

    def test_cancelled_does_not_block(self):
        created = self.create_via_api()
        client = self.client_for(self.owner)
        cancel = client.post(reverse('reservation-cancel', args=[created.data['id']]), {}, format='json')
        self.assertEqual(cancel.status_code, status.HTTP_200_OK)
        self.create_via_api(customer_name='Replacement', start_time='19:00:00')

    def test_no_show_does_not_block(self):
        created = self.create_via_api()
        client = self.client_for(self.owner)
        noshow = client.post(reverse('reservation-no-show', args=[created.data['id']]), {}, format='json')
        self.assertEqual(noshow.status_code, status.HTTP_200_OK)
        self.create_via_api(customer_name='Walkin', start_time='19:00:00')

    def test_edit_does_not_conflict_with_self(self):
        created = self.create_via_api()
        client = self.client_for(self.owner)
        url = reverse('reservation-detail', args=[created.data['id']])
        res = client.patch(url, {'notes': 'Updated notes', 'guest_count': 2}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data['notes'], 'Updated notes')

    def test_edit_into_other_range_rejected(self):
        first = self.create_via_api(start_time='19:00:00', expected_duration_minutes=90)
        second = self.create_via_api(customer_name='Later', start_time='21:00:00', expected_duration_minutes=60)
        client = self.client_for(self.owner)
        url = reverse('reservation-detail', args=[second.data['id']])
        res = client.patch(url, {'start_time': '19:30:00'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', res.data)

    def test_change_table_checks_new_table(self):
        self.create_via_api(table=self.table2.id, start_time='19:00:00')
        moving = self.create_via_api(customer_name='Mover', start_time='19:00:00')
        client = self.client_for(self.owner)
        url = reverse('reservation-detail', args=[moving.data['id']])
        res = client.patch(url, {'table': self.table2.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('table', res.data)
        ok = client.patch(url, {'table': self.table2.id, 'start_time': '21:00:00'}, format='json')
        self.assertEqual(ok.status_code, status.HTTP_200_OK, ok.data)
        self.assertTrue(ReservationHistory.objects.filter(reservation_id=moving.data['id'], action='TABLE_CHANGED').exists())

    def test_check_in_and_invalid_transitions(self):
        created = self.create_via_api()
        client = self.client_for(self.owner)
        pk = created.data['id']
        bad_complete = client.post(reverse('reservation-complete', args=[pk]), {}, format='json')
        self.assertEqual(bad_complete.status_code, status.HTTP_400_BAD_REQUEST)
        check_in = client.post(reverse('reservation-check-in', args=[pk]), {}, format='json')
        self.assertEqual(check_in.status_code, status.HTTP_200_OK)
        self.assertEqual(check_in.data['status'], 'CHECKED_IN')
        self.assertTrue(ReservationHistory.objects.filter(reservation_id=pk, action='CHECKED_IN').exists())
        patch_status = client.patch(reverse('reservation-detail', args=[pk]), {'status': 'CANCELLED'}, format='json')
        self.assertEqual(patch_status.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_status.data['status'], 'CHECKED_IN')

    def test_cancellation_preserves_history(self):
        created = self.create_via_api()
        pk = created.data['id']
        client = self.client_for(self.owner)
        client.post(reverse('reservation-cancel', args=[pk]), {}, format='json')
        self.assertEqual(Reservation.objects.get(pk=pk).status, 'CANCELLED')
        self.assertTrue(ReservationHistory.objects.filter(reservation_id=pk, action='CREATED').exists())
        self.assertTrue(ReservationHistory.objects.filter(reservation_id=pk, action='CANCELLED').exists())
        delete = client.delete(reverse('reservation-detail', args=[pk]))
        self.assertEqual(delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Reservation.objects.filter(pk=pk).exists())

    def test_no_show_and_complete_preserve_history(self):
        noshow = self.create_via_api(customer_name='NoShow')
        complete = self.create_via_api(customer_name='Diner', start_time='12:00:00')
        client = self.client_for(self.manager)
        client.post(reverse('reservation-no-show', args=[noshow.data['id']]), {}, format='json')
        client.post(reverse('reservation-check-in', args=[complete.data['id']]), {}, format='json')
        client.post(reverse('reservation-complete', args=[complete.data['id']]), {}, format='json')
        self.assertTrue(ReservationHistory.objects.filter(reservation_id=noshow.data['id'], action='NO_SHOW').exists())
        self.assertTrue(ReservationHistory.objects.filter(reservation_id=complete.data['id'], action='COMPLETED').exists())
        self.assertEqual(Reservation.objects.get(pk=noshow.data['id']).status, 'NO_SHOW')
        self.assertEqual(Reservation.objects.get(pk=complete.data['id']).status, 'COMPLETED')

    def test_actor_recorded_on_history(self):
        created = self.create_via_api(user=self.waiter)
        history = ReservationHistory.objects.get(reservation_id=created.data['id'], action='CREATED')
        self.assertEqual(history.performed_by_id, self.waiter.id)

    def test_rbac_owner_manager_waiter_cashier_kitchen(self):
        client_owner = self.client_for(self.owner)
        client_mgr = self.client_for(self.manager)
        client_waiter = self.client_for(self.waiter)
        client_cashier = self.client_for(self.cashier)
        client_kitchen = self.client_for(self.kitchen)

        self.assertEqual(client_kitchen.get(self.list_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(client_cashier.get(self.list_url).status_code, status.HTTP_200_OK)

        owner_res = client_owner.post(self.list_url, self.payload(customer_name='OwnerBook'), format='json')
        self.assertEqual(owner_res.status_code, status.HTTP_201_CREATED)
        mgr_res = client_mgr.post(self.list_url, self.payload(customer_name='MgrBook', start_time='12:00:00'), format='json')
        self.assertEqual(mgr_res.status_code, status.HTTP_201_CREATED)
        waiter_res = client_waiter.post(self.list_url, self.payload(customer_name='WaiterBook', start_time='14:00:00'), format='json')
        self.assertEqual(waiter_res.status_code, status.HTTP_201_CREATED)

        cashier_create = client_cashier.post(self.list_url, self.payload(customer_name='CashierBook', start_time='16:00:00'), format='json')
        self.assertEqual(cashier_create.status_code, status.HTTP_403_FORBIDDEN)
        kitchen_create = client_kitchen.post(self.list_url, self.payload(customer_name='KitchenBook', start_time='16:00:00'), format='json')
        self.assertEqual(kitchen_create.status_code, status.HTTP_403_FORBIDDEN)

        pk = waiter_res.data['id']
        self.assertEqual(client_cashier.post(reverse('reservation-check-in', args=[pk]), {}, format='json').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(client_kitchen.post(reverse('reservation-check-in', args=[pk]), {}, format='json').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(client_waiter.post(reverse('reservation-check-in', args=[pk]), {}, format='json').status_code, status.HTTP_200_OK)
        self.assertEqual(client_waiter.get(reverse('reservation-history', args=[pk])).status_code, status.HTTP_200_OK)

        cashier_patch = client_cashier.patch(reverse('reservation-detail', args=[pk]), {'notes': 'hack'}, format='json')
        self.assertEqual(cashier_patch.status_code, status.HTTP_403_FORBIDDEN)

    def test_midnight_crossing_rejected(self):
        client = self.client_for(self.owner)
        res = client.post(self.list_url, self.payload(start_time='23:00:00', expected_duration_minutes=180), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expected_duration_minutes', res.data)

    def test_filters(self):
        self.create_via_api(customer_name='FilterMe', customer_contact='01811111111')
        client = self.client_for(self.owner)
        listed = client.get(self.list_url, {'customer_name': 'Filter', 'status': 'RESERVED', 'table': self.table1.id})
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)

    def test_complete_does_not_free_table_with_active_order(self):
        created = self.create_via_api(start_time='18:00:00')
        client = self.client_for(self.owner)
        pk = created.data['id']
        client.post(reverse('reservation-check-in', args=[pk]), {}, format='json')
        Order.objects.create(restaurant=self.restaurant, table=self.table1, status='open', total_amount=0)
        self.table1.status = 'occupied'
        self.table1.save()
        client.post(reverse('reservation-complete', args=[pk]), {}, format='json')
        self.table1.refresh_from_db()
        self.assertEqual(self.table1.status, 'occupied')

    def test_table_rename_does_not_break_reservation(self):
        created = self.create_via_api()
        self.table1.name = 'VIP-1'
        self.table1.save()
        client = self.client_for(self.owner)
        detail = client.get(reverse('reservation-detail', args=[created.data['id']]))
        self.assertEqual(detail.data['table'], self.table1.id)
        self.assertEqual(detail.data['table_name'], 'VIP-1')
