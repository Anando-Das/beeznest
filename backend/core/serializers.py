from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from .models import Restaurant, Category, MenuItem, MenuItemPriceHistory, Table, Order, OrderItem, Customer, Expense, DayClose, Zone, Reservation, ReservationHistory, LayoutObject, Payment

User = get_user_model()

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'address', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'restaurant', 'is_active']
        read_only_fields = ['id', 'role', 'restaurant']

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    restaurant_name = serializers.CharField(write_only=True, required=True, max_length=255)
    restaurant_address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'restaurant_name', 'restaurant_address']
        
    def create(self, validated_data):
        restaurant_name = validated_data.pop('restaurant_name')
        restaurant_address = validated_data.pop('restaurant_address', '')
        
        from django.db import transaction
        with transaction.atomic():
            restaurant = Restaurant.objects.create(
                name=restaurant_name,
                address=restaurant_address
            )
            
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data.get('email', ''),
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                restaurant=restaurant,
                role='OWNER'
            )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class MenuItemPriceHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    class Meta:
        model = MenuItemPriceHistory
        fields = '__all__'
        read_only_fields = ['id', 'changed_at', 'changed_by', 'menu_item']

class CategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'sort_order', 'created_at', 'updated_at', 'items']
        read_only_fields = ['id', 'created_at', 'updated_at']

class TableSerializer(serializers.ModelSerializer):
    zone_name = serializers.SerializerMethodField()
    current_reservation = serializers.SerializerMethodField()
    operational_status = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = '__all__'
        read_only_fields = ['id', 'restaurant']

    def _todays_reservation(self, obj):
        cached = getattr(obj, 'todays_active_reservations', None)
        if cached is not None:
            return cached[0] if cached else None
        today = timezone.localdate()
        return obj.reservations.filter(
            reservation_date=today,
            status__in=['RESERVED', 'CHECKED_IN'],
        ).order_by('start_time').first()

    def get_zone_name(self, obj):
        return obj.zone.name if obj.zone_id else None

    def get_current_reservation(self, obj):
        res = self._todays_reservation(obj)
        if not res:
            return None
        return {
            'id': res.id,
            'customer_name': res.customer_name,
            'customer_contact': res.customer_contact,
            'status': res.status,
            'start_time': res.start_time,
            'guest_count': res.guests,
            'expected_duration_minutes': res.expected_duration_minutes,
        }

    def get_operational_status(self, obj):
        if not obj.is_active:
            return 'inactive'
        if obj.status == 'occupied':
            return 'occupied'
        res = self._todays_reservation(obj)
        if res:
            return 'reserved' if res.status == 'RESERVED' else 'occupied'
        if obj.status == 'reserved':
            return 'reserved'
        return 'available'

    def validate(self, data):
        # Table name uniqueness per restaurant
        name = data.get('name')
        if name:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.restaurant:
                restaurant = request.user.restaurant
                qs = Table.objects.filter(name__iexact=name, restaurant=restaurant)
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise serializers.ValidationError({"name": "A table with this name already exists."})

        # Capacity > 0
        seats = data.get('seats')
        if seats is not None and seats <= 0:
            raise serializers.ValidationError({"seats": "Capacity must be greater than 0."})

        # Zone must be active
        zone = data.get('zone')
        if zone and not zone.is_active:
            # allow updating an existing table that is already in an inactive zone, 
            # as long as we aren't changing it *to* an inactive zone
            if not (self.instance and self.instance.zone == zone):
                raise serializers.ValidationError({"zone": "Cannot assign a table to an inactive zone."})

        return data

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    price_at_time = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['id']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'amount', 'method', 'processed_by', 'timestamp']
        read_only_fields = ['id', 'order', 'processed_by', 'timestamp']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    table_name = serializers.CharField(source='table.name', read_only=True, allow_null=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True, allow_null=True)
    payment = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at', 'total_amount', 'customer']

    def get_payment(self, obj):
        from django.db.utils import ProgrammingError
        from django.core.exceptions import ObjectDoesNotExist
        try:
            return PaymentSerializer(obj.payment).data
        except (ObjectDoesNotExist, ProgrammingError):
            return None

class OrderItemCreateSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'notes', 'menu_item_name']
        read_only_fields = ['id']

class OrderItemUpdateSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'notes', 'menu_item_name']
        read_only_fields = ['id', 'price_at_time']  # Price cannot be changed on update

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    class Meta:
        model = Order
        fields = ['table', 'order_type', 'status', 'items', 'customer_phone']
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at', 'total_amount']
    
    def validate_table(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError("Cannot create an order on an inactive table.")
        return value
    
    def validate_items(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one item is required.")
        return value
    
    def validate(self, data):
        table = data.get('table')
        items = data.get('items', [])
        
        request = self.context.get('request')
        if not request or not request.user.restaurant:
            raise serializers.ValidationError("User must belong to a restaurant.")
        
        restaurant = request.user.restaurant
        
        # Validate table belongs to restaurant
        if table and table.restaurant != restaurant:
            raise serializers.ValidationError({"table": "Table does not belong to your restaurant."})
        
        # Validate all menu items belong to restaurant and are available
        for item_data in items:
            menu_item = item_data.get('menu_item')
            if not menu_item:
                continue
            
            if menu_item.category.restaurant != restaurant:
                raise serializers.ValidationError({
                    "items": f"Menu item '{menu_item.name}' does not belong to your restaurant."
                })
            
            if not menu_item.is_available:
                raise serializers.ValidationError({
                    "items": f"Menu item '{menu_item.name}' is not available."
                })
        
        return data

class OrderUpdateSerializer(serializers.ModelSerializer):
    items = OrderItemUpdateSerializer(many=True, required=False)
    
    class Meta:
        model = Order
        fields = ['status', 'items']
        read_only_fields = ['id', 'restaurant', 'table', 'order_type', 'created_at', 'updated_at', 'total_amount']
    
    def validate_status(self, value):
        instance = self.instance
        if instance.status in ['paid', 'cancelled']:
            raise serializers.ValidationError(
                f"Cannot modify an order that is {instance.status}."
            )
        if value == 'paid':
            raise serializers.ValidationError("Payments must be processed through the dedicated payment endpoint.")
        return value
    
    def validate_items(self, value):
        if value is not None and len(value) == 0:
            raise serializers.ValidationError("Order must have at least one item.")
        return value
    
    def validate(self, data):
        items = data.get('items')
        request = self.context.get('request')
        
        if items:
            restaurant = request.user.restaurant
            
            # Validate all menu items belong to restaurant and are available
            for item_data in items:
                menu_item = item_data.get('menu_item')
                if not menu_item:
                    continue
                
                if menu_item.category.restaurant != restaurant:
                    raise serializers.ValidationError({
                        "items": f"Menu item '{menu_item.name}' does not belong to your restaurant."
                    })
                
                if not menu_item.is_available:
                    raise serializers.ValidationError({
                        "items": f"Menu item '{menu_item.name}' is not available."
                    })
        
        return data

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'created_at']

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'date']

class DayCloseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayClose
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'date']

class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'role', 'email']
        
    def validate_role(self, value):
        if value not in ['OWNER', 'MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']:
            raise serializers.ValidationError("Invalid role.")
        return value

class StaffUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'is_active']
        
    def validate_role(self, value):
        if value not in ['OWNER', 'MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']:
            raise serializers.ValidationError("Invalid role.")
        return value



class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at']

class LayoutObjectSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)

    class Meta:
        model = LayoutObject
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at']

    def validate(self, data):
        # Zone must be active
        zone = data.get('zone')
        if zone and not zone.is_active:
            # allow updating an existing object that is already in an inactive zone,
            # as long as we aren't changing it *to* an inactive zone
            if not (self.instance and self.instance.zone == zone):
                raise serializers.ValidationError({"zone": "Cannot assign to an inactive zone."})
        return data

class ReservationHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source='performed_by.username', read_only=True)

    class Meta:
        model = ReservationHistory
        fields = [
            'id', 'action', 'previous_values', 'new_values',
            'performed_by', 'performed_by_name', 'reason', 'created_at',
        ]
        read_only_fields = fields


class ReservationSerializer(serializers.ModelSerializer):
    table_name = serializers.CharField(source='table.name', read_only=True)
    table_seats = serializers.IntegerField(source='table.seats', read_only=True)
    table_is_active = serializers.BooleanField(source='table.is_active', read_only=True)
    zone_name = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    guest_count = serializers.IntegerField(source='guests')
    end_time = serializers.SerializerMethodField()
    confirm_over_capacity = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Reservation
        fields = [
            'id', 'restaurant', 'customer_name', 'customer_contact', 'table',
            'table_name', 'table_seats', 'table_is_active', 'zone_name',
            'reservation_date', 'start_time', 'expected_duration_minutes', 'end_time',
            'guest_count', 'notes', 'status',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at', 'confirm_over_capacity',
        ]
        read_only_fields = [
            'id', 'restaurant', 'created_by', 'updated_by', 'created_at', 'updated_at', 'status',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        restaurant = getattr(getattr(request, 'user', None), 'restaurant', None)
        if restaurant:
            self.fields['table'].queryset = Table.objects.filter(restaurant=restaurant)

    def get_zone_name(self, obj):
        zone = getattr(obj.table, 'zone', None)
        return zone.name if zone else None

    def get_end_time(self, obj):
        end_dt = obj.end_datetime()
        return end_dt.time().strftime('%H:%M:%S')

    def validate(self, data):
        from . import reservation_service as svc

        confirm = data.pop('confirm_over_capacity', False)
        instance = self.instance

        res_date = data.get('reservation_date', getattr(instance, 'reservation_date', None))
        start_time = data.get('start_time', getattr(instance, 'start_time', None))
        duration = data.get('expected_duration_minutes', getattr(instance, 'expected_duration_minutes', 120))
        table = data.get('table', getattr(instance, 'table', None))
        guest_count = data.get('guests', getattr(instance, 'guests', None))

        schedule_fields = {'reservation_date', 'start_time', 'expected_duration_minutes', 'table', 'guests'}
        schedule_changing = instance is None or bool(schedule_fields.intersection(data.keys()))

        if not table:
            raise serializers.ValidationError({'table': ['A valid table is required.']})

        svc.assert_table_active_for_new_booking(
            table,
            is_create=instance is None,
            previous_table=getattr(instance, 'table', None),
        )

        if guest_count is not None and schedule_changing:
            svc.assert_guest_count(guest_count, table, confirm)

        if instance is None or any(k in data for k in ('reservation_date', 'start_time', 'expected_duration_minutes', 'table')):
            if not res_date or not start_time:
                raise serializers.ValidationError({
                    'reservation_date': ['Date and start time are required.']
                })
            window_error = svc.booking_window_error(res_date)
            if window_error:
                raise serializers.ValidationError({'reservation_date': [window_error]})
            start_dt, end_dt = svc.interval_for(res_date, start_time, duration)
            status_val = getattr(instance, 'status', 'RESERVED')
            if status_val in svc.ACTIVE_STATUSES:
                svc.assert_no_overlap(
                    table, res_date, start_dt, end_dt,
                    exclude_id=getattr(instance, 'id', None),
                )

        data['_confirm_over_capacity'] = confirm
        return data

    def create(self, validated_data):
        from . import reservation_service as svc
        validated_data.pop('_confirm_over_capacity', None)
        request = self.context['request']
        with transaction.atomic():
            table = svc.lock_table(validated_data['table'].pk)
            validated_data['table'] = table
            svc.assert_table_active_for_new_booking(table, is_create=True)
            start_dt, end_dt = svc.interval_for(
                validated_data['reservation_date'],
                validated_data['start_time'],
                validated_data.get('expected_duration_minutes', 120),
            )
            svc.assert_no_overlap(table, validated_data['reservation_date'], start_dt, end_dt)
            svc.assert_guest_count(
                validated_data.get('guests', 2),
                table,
                confirm_over_capacity=True,
            )
            reservation = Reservation.objects.create(**validated_data)
            svc.log_history(
                reservation, 'CREATED', request.user,
                new_values=svc.snapshot(reservation),
            )
            svc.sync_table_after_reservation_change(reservation)
            return reservation

    def update(self, instance, validated_data):
        from . import reservation_service as svc
        validated_data.pop('_confirm_over_capacity', None)
        request = self.context['request']
        previous = svc.snapshot(instance)
        previous_table = instance.table
        with transaction.atomic():
            new_table = validated_data.get('table', instance.table)
            table = svc.lock_table(new_table.pk)
            validated_data['table'] = table
            res_date = validated_data.get('reservation_date', instance.reservation_date)
            start_time = validated_data.get('start_time', instance.start_time)
            duration = validated_data.get('expected_duration_minutes', instance.expected_duration_minutes)
            start_dt, end_dt = svc.interval_for(res_date, start_time, duration)
            if instance.status in svc.ACTIVE_STATUSES:
                svc.assert_no_overlap(table, res_date, start_dt, end_dt, exclude_id=instance.pk)
            validated_data['updated_by'] = request.user
            reservation = super().update(instance, validated_data)
            new_snap = svc.snapshot(reservation)
            table_changed = previous['table_id'] != new_snap['table_id']
            svc.log_history(
                reservation,
                'TABLE_CHANGED' if table_changed else 'EDITED',
                request.user,
                previous_values=previous,
                new_values=new_snap,
            )
            svc.sync_table_after_reservation_change(reservation, previous_table=previous_table)
            return reservation
