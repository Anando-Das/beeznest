import os
import re

MODELS_PATH = 'core/models.py'
SERIALIZERS_PATH = 'core/serializers.py'
VIEWS_PATH = 'core/views.py'
URLS_PATH = 'core/urls.py'

def patch_models():
    with open(MODELS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    zone_model = """
class Zone(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
"""
    
    table_old = """class Table(models.Model):
    STATUS_CHOICES = [
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50)
    seats = models.IntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='free')

    def __str__(self):
        return f"{self.name} ({self.seats} seats)"
"""

    table_new = """class Table(models.Model):
    STATUS_CHOICES = [
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
    ]
    SHAPE_CHOICES = [
        ('RECTANGLE', 'Rectangle'),
        ('SQUARE', 'Square'),
        ('CIRCLE', 'Circle'),
        ('OVAL', 'Oval'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50)
    seats = models.IntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='free')
    
    zone = models.ForeignKey('Zone', on_delete=models.SET_NULL, null=True, blank=True, related_name='tables')
    shape = models.CharField(max_length=20, choices=SHAPE_CHOICES, default='RECTANGLE')
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.seats} seats)"
"""

    reservation_model = """
class Reservation(models.Model):
    STATUS_CHOICES = [
        ('RESERVED', 'Reserved'),
        ('CHECKED_IN', 'Checked In'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
        ('CANCELLED', 'Cancelled'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reservations')
    customer_name = models.CharField(max_length=255)
    customer_contact = models.CharField(max_length=255, blank=True, null=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateField()
    start_time = models.TimeField()
    expected_duration_minutes = models.IntegerField(default=120)
    guests = models.IntegerField(default=2)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RESERVED')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_reservations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_name} - {self.table.name} at {self.reservation_date} {self.start_time}"
"""

    if 'class Zone' not in content:
        # Insert Zone before Table
        content = content.replace(table_old, zone_model + '\n' + table_new)
    
    if 'class Reservation' not in content:
        content += reservation_model

    # Add missing django.utils timezone if needed
    if 'timezone' not in content:
        content = 'from django.utils import timezone\n' + content

    with open(MODELS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)


def patch_serializers():
    with open(SERIALIZERS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'ZoneSerializer' not in content:
        zone_ser = """
class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at']

class ReservationSerializer(serializers.ModelSerializer):
    table_name = serializers.CharField(source='table.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'created_by', 'created_at', 'updated_at']
"""
        # Add imports
        content = content.replace(
            'from .models import Restaurant, Category, MenuItem, MenuItemPriceHistory, Table, Order, OrderItem, Customer, Expense, DayClose',
            'from .models import Restaurant, Category, MenuItem, MenuItemPriceHistory, Table, Order, OrderItem, Customer, Expense, DayClose, Zone, Reservation'
        )
        content += zone_ser

    with open(SERIALIZERS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)


def patch_views():
    with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'ZoneViewSet' not in content:
        # Add imports
        content = content.replace(
            'from .models import Category, MenuItem, MenuItemPriceHistory, Table, Order, OrderItem, Customer, Expense, DayClose',
            'from .models import Category, MenuItem, MenuItemPriceHistory, Table, Order, OrderItem, Customer, Expense, DayClose, Zone, Reservation'
        )
        content = content.replace(
            'from .serializers import CategorySerializer, MenuItemSerializer, MenuItemPriceHistorySerializer, TableSerializer, OrderSerializer, OrderItemSerializer, CustomerSerializer, ExpenseSerializer, DayCloseSerializer, StaffCreateSerializer, StaffUpdateSerializer',
            'from .serializers import CategorySerializer, MenuItemSerializer, MenuItemPriceHistorySerializer, TableSerializer, OrderSerializer, OrderItemSerializer, CustomerSerializer, ExpenseSerializer, DayCloseSerializer, StaffCreateSerializer, StaffUpdateSerializer, ZoneSerializer, ReservationSerializer'
        )
        
        view_str = """
class ZoneViewSet(RestaurantScopedViewSet):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']

class ReservationViewSet(RestaurantScopedViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    read_roles = ['MANAGER', 'WAITER', 'CASHIER']
    write_roles = ['MANAGER', 'WAITER']
    
    def perform_create(self, serializer):
        table = serializer.validated_data['table']
        if not table.is_active:
            raise serializers.ValidationError({"table": "Cannot reserve an inactive table."})
        super().perform_create(serializer)
        serializer.instance.created_by = self.request.user
        serializer.instance.save()
"""
        content += view_str
        
        # Add transfer and merge actions to TableViewSet
        table_viewset_old = """class TableViewSet(RestaurantScopedViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']"""
        
        table_viewset_new = """class TableViewSet(RestaurantScopedViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def transfer(self, request, pk=None):
        user = request.user
        if user.role not in ['OWNER', 'MANAGER', 'WAITER']:
            raise PermissionDenied("You do not have permission to transfer tables.")
        
        table = self.get_object()
        new_table_id = request.data.get('new_table_id')
        try:
            new_table = Table.objects.get(id=new_table_id, restaurant=user.restaurant)
        except Table.DoesNotExist:
            return Response({"detail": "Destination table not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if not new_table.is_active:
            return Response({"detail": "Destination table is inactive."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Move active orders from table to new_table
        active_orders = Order.objects.filter(table=table, status__in=['open', 'preparing', 'served'])
        if not active_orders.exists():
            return Response({"detail": "No active orders to transfer."}, status=status.HTTP_400_BAD_REQUEST)
            
        for order in active_orders:
            order.table = new_table
            order.save()
            
        table.status = 'free'
        table.save()
        new_table.status = 'occupied'
        new_table.save()
        
        return Response({"detail": "Transferred successfully."})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def merge(self, request, pk=None):
        user = request.user
        if user.role not in ['OWNER', 'MANAGER', 'WAITER']:
            raise PermissionDenied("You do not have permission to merge tables.")
            
        table = self.get_object()
        merge_table_id = request.data.get('merge_table_id')
        try:
            merge_table = Table.objects.get(id=merge_table_id, restaurant=user.restaurant)
        except Table.DoesNotExist:
            return Response({"detail": "Table to merge not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if not merge_table.is_active:
            return Response({"detail": "Cannot merge with inactive table."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get active order on table
        table_orders = Order.objects.filter(table=table, status__in=['open', 'preparing', 'served'])
        merge_table_orders = Order.objects.filter(table=merge_table, status__in=['open', 'preparing', 'served'])
        
        if not table_orders.exists() and not merge_table_orders.exists():
            return Response({"detail": "No active orders to merge."}, status=status.HTTP_400_BAD_REQUEST)
            
        primary_order = table_orders.first()
        secondary_order = merge_table_orders.first()
        
        if not primary_order:
            primary_order = secondary_order
            secondary_order = None
            
        if primary_order and secondary_order:
            # move items from secondary to primary
            from django.db import transaction
            with transaction.atomic():
                for item in secondary_order.items.all():
                    item.order = primary_order
                    item.save()
                
                # update primary total
                total = sum(i.quantity * i.price_at_time for i in primary_order.items.all())
                primary_order.total_amount = total
                primary_order.save()
                
                secondary_order.status = 'cancelled'
                secondary_order.save()
                
                merge_table.status = 'free'
                merge_table.save()
                
        return Response({"detail": "Merged successfully."})
"""
        content = content.replace(table_viewset_old, table_viewset_new)

    with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def patch_urls():
    with open(URLS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'ZoneViewSet' not in content:
        content = content.replace(
            "router.register(r'tables', TableViewSet, basename='table')",
            "router.register(r'tables', TableViewSet, basename='table')\nrouter.register(r'zones', ZoneViewSet, basename='zone')\nrouter.register(r'reservations', ReservationViewSet, basename='reservation')"
        )
        content = content.replace(
            'from .views import SignupView',
            'from .views import ZoneViewSet, ReservationViewSet, SignupView'
        )
        
    with open(URLS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    patch_models()
    patch_serializers()
    patch_views()
    patch_urls()
    print("Backend patched successfully")
