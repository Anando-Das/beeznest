from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Restaurant, Category, MenuItem, Table, Order, OrderItem, Customer, Expense, DayClose

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
        read_only_fields = ['id']

class CategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'name', 'sort_order', 'items']
        read_only_fields = ['id']

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'
        read_only_fields = ['id', 'restaurant']

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['id', 'order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    table_name = serializers.CharField(source='table.name', read_only=True)
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at']

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


