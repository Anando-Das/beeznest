"""Reservation domain rules. Used by serializers, views, and tests.

Waiter policy: waiters may view, create, and edit operational reservation fields
(customer, contact, table, date, time, duration, guest count, notes), and may
check in, cancel, mark no-show, and complete. They cannot hard-delete records
or use status-correction. Cashiers are read-only. Kitchen has no reservation access.
"""
import datetime

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Order, Reservation, ReservationHistory, Table

MAX_ADVANCE_DAYS = 30
ACTIVE_STATUSES = Reservation.ACTIVE_STATUSES
ACTIVE_ORDER_STATUSES = ('open', 'preparing', 'served')

ALLOWED_TRANSITIONS = {
    'RESERVED': frozenset({'CHECKED_IN', 'NO_SHOW', 'CANCELLED'}),
    'CHECKED_IN': frozenset({'COMPLETED'}),
    'COMPLETED': frozenset(),
    'NO_SHOW': frozenset(),
    'CANCELLED': frozenset(),
}

STATUS_ACTION_MAP = {
    'CHECKED_IN': 'CHECKED_IN',
    'NO_SHOW': 'NO_SHOW',
    'CANCELLED': 'CANCELLED',
    'COMPLETED': 'COMPLETED',
}


def snapshot(reservation):
    return {
        'customer_name': reservation.customer_name,
        'customer_contact': reservation.customer_contact,
        'table_id': reservation.table_id,
        'reservation_date': str(reservation.reservation_date),
        'start_time': str(reservation.start_time)[:8],
        'expected_duration_minutes': reservation.expected_duration_minutes,
        'guest_count': reservation.guests,
        'notes': reservation.notes,
        'status': reservation.status,
    }


def log_history(reservation, action, performed_by, previous_values=None, new_values=None, reason=None):
    return ReservationHistory.objects.create(
        reservation=reservation,
        action=action,
        previous_values=previous_values,
        new_values=new_values,
        performed_by=performed_by,
        reason=reason,
    )


def local_today():
    """Restaurant-local calendar date from Django TIME_ZONE (not the browser clock)."""
    return timezone.localdate()


def booking_window_error(reservation_date):
    today = local_today()
    if reservation_date < today:
        return 'Cannot reserve a date in the past.'
    if reservation_date > today + datetime.timedelta(days=MAX_ADVANCE_DAYS):
        return f'Cannot reserve more than {MAX_ADVANCE_DAYS} days in advance.'
    return None


def interval_for(reservation_date, start_time, duration_minutes):
    if duration_minutes is None or duration_minutes <= 0:
        raise ValidationError({'expected_duration_minutes': ['Duration must be a positive number of minutes.']})
    start_dt = datetime.datetime.combine(reservation_date, start_time)
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
    if end_dt.date() != reservation_date:
        raise ValidationError({
            'expected_duration_minutes': [
                'Reservations cannot cross midnight. Shorten the duration or choose an earlier start time.'
            ]
        })
    if end_dt <= start_dt:
        raise ValidationError({'expected_duration_minutes': ['End time must be after start time.']})
    return start_dt, end_dt


def intervals_overlap(start_a, end_a, start_b, end_b):
    # Adjacent intervals that only touch at the boundary are allowed.
    return start_a < end_b and end_a > start_b


def overlapping_reservations(table, reservation_date, start_dt, end_dt, exclude_id=None):
    qs = Reservation.objects.filter(
        table=table,
        reservation_date=reservation_date,
        status__in=ACTIVE_STATUSES,
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    conflicts = []
    for other in qs:
        other_start = datetime.datetime.combine(other.reservation_date, other.start_time)
        other_end = other_start + datetime.timedelta(minutes=other.expected_duration_minutes)
        if intervals_overlap(start_dt, end_dt, other_start, other_end):
            conflicts.append(other)
    return conflicts


def assert_no_overlap(table, reservation_date, start_dt, end_dt, exclude_id=None):
    conflicts = overlapping_reservations(table, reservation_date, start_dt, end_dt, exclude_id=exclude_id)
    if conflicts:
        other = conflicts[0]
        raise ValidationError({
            'table': [
                f'Table {other.table.name} is already reserved from {other.start_time.strftime("%H:%M")} '
                f'({other.expected_duration_minutes} min) for {other.customer_name}.'
            ]
        })


def assert_table_active_for_new_booking(table, is_create, previous_table=None):
    assigning_new = is_create or (previous_table is not None and previous_table.pk != table.pk)
    if assigning_new and not table.is_active:
        raise ValidationError({'table': ['Cannot create a reservation on an inactive table.']})


def capacity_confirmation_error(guest_count, table):
    return ValidationError({
        'guest_count': [
            f'Guest count ({guest_count}) exceeds table capacity ({table.seats}). '
            'Resubmit with confirm_over_capacity=true to continue.'
        ],
        'requires_capacity_confirmation': [True],
        'table_capacity': [table.seats],
    })


def assert_guest_count(guest_count, table, confirm_over_capacity):
    if guest_count is None or guest_count < 1:
        raise ValidationError({'guest_count': ['Guest count must be a positive integer.']})
    if guest_count > table.seats and not confirm_over_capacity:
        raise capacity_confirmation_error(guest_count, table)


def table_has_active_order(table):
    return Order.objects.filter(table=table, status__in=ACTIVE_ORDER_STATUSES).exists()


def other_active_reservations(table, reservation_date, exclude_id=None):
    qs = Reservation.objects.filter(
        table=table,
        reservation_date=reservation_date,
        status__in=ACTIVE_STATUSES,
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


def lock_table(table_id):
    return Table.objects.select_for_update().get(pk=table_id)


def sync_table_after_reservation_change(reservation, previous_table=None):
    """Adjust table.status without overwriting occupied tables that have active orders.

    Existing table statuses are free / occupied / reserved plus is_active.
    BILLING is not implemented yet (POS phase).
    """
    tables = [reservation.table]
    if previous_table and previous_table.pk != reservation.table.pk:
        tables.append(previous_table)

    today = local_today()
    for table in tables:
        if table_has_active_order(table):
            if table.status != 'occupied':
                table.status = 'occupied'
                table.save(update_fields=['status', 'updated_at'])
            continue

        active_today = Reservation.objects.filter(
            table=table,
            reservation_date=today,
            status__in=ACTIVE_STATUSES,
        )
        checked_in = active_today.filter(status='CHECKED_IN').exists()
        reserved = active_today.filter(status='RESERVED').exists()

        if checked_in:
            desired = 'occupied'
        elif reserved:
            desired = 'reserved'
        else:
            desired = 'free'

        if table.status != desired:
            table.status = desired
            table.save(update_fields=['status', 'updated_at'])


def sync_table_status_for_orders(table):
    """Sync table.status based on active orders and reservations.
    
    Used after order creation/cancellation to ensure table status reflects reality.
    """
    if not table.is_active:
        return
    
    today = local_today()
    
    # Check for active orders
    if table_has_active_order(table):
        if table.status != 'occupied':
            table.status = 'occupied'
            table.save(update_fields=['status', 'updated_at'])
        return
    
    # Check for active reservations
    active_today = Reservation.objects.filter(
        table=table,
        reservation_date=today,
        status__in=ACTIVE_STATUSES,
    )
    checked_in = active_today.filter(status='CHECKED_IN').exists()
    reserved = active_today.filter(status='RESERVED').exists()
    
    if checked_in:
        desired = 'occupied'
    elif reserved:
        desired = 'reserved'
    else:
        desired = 'free'
    
    if table.status != desired:
        table.status = desired
        table.save(update_fields=['status', 'updated_at'])


def apply_status_transition(reservation, new_status, user, reason=None, allow_correction=False):
    current = reservation.status
    if current == new_status:
        raise ValidationError({'status': [f'Reservation is already {new_status}.']})

    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if new_status not in allowed:
        if not allow_correction:
            raise ValidationError({
                'status': [f'Cannot change status from {current} to {new_status}.']
            })
        if not reason:
            raise ValidationError({'reason': ['A reason is required to correct reservation status.']})

    previous = snapshot(reservation)
    reservation.status = new_status
    reservation.updated_by = user
    reservation.save(update_fields=['status', 'updated_by', 'updated_at'])
    action = 'CORRECTED' if new_status not in allowed else STATUS_ACTION_MAP[new_status]
    log_history(
        reservation,
        action,
        user,
        previous_values=previous,
        new_values=snapshot(reservation),
        reason=reason,
    )
    sync_table_after_reservation_change(reservation)
    return reservation
