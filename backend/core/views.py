from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from .serializers import SignupSerializer, LoginSerializer, UserSerializer, RestaurantSerializer
from .models import Restaurant

class CSRFTokenView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'csrfToken': get_token(request)})

class SignupView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

class MeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class RestaurantOnboardingView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.restaurant:
            return Response({"detail": "User already has a restaurant."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = RestaurantSerializer(data=request.data)
        if serializer.is_valid():
            restaurant = serializer.save()
            request.user.restaurant = restaurant
            request.user.role = 'OWNER'
            request.user.save()
            return Response(UserSerializer(request.user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import Category, MenuItem, Table, Order, OrderItem, Customer, Expense, DayClose
from .serializers import CategorySerializer, MenuItemSerializer, TableSerializer, OrderSerializer, OrderItemSerializer, CustomerSerializer, ExpenseSerializer, DayCloseSerializer, StaffCreateSerializer, StaffUpdateSerializer
from .permissions import RoleBasedAccess, IsOwnerOnly
from rest_framework.decorators import action

class RestaurantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RoleBasedAccess]
    def get_queryset(self):
        if not self.request.user.restaurant:
            return self.queryset.none()
        return self.queryset.filter(restaurant=self.request.user.restaurant)
    def perform_create(self, serializer):
        if not self.request.user.restaurant:
            raise PermissionDenied("You must belong to a restaurant to perform this action.")
        serializer.save(restaurant=self.request.user.restaurant)

class CategoryViewSet(RestaurantScopedViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']

class MenuItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RoleBasedAccess]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']
    def get_queryset(self):
        if not self.request.user.restaurant:
            return self.queryset.none()
        return self.queryset.filter(category__restaurant=self.request.user.restaurant)
    def perform_create(self, serializer):
        category = serializer.validated_data.get('category')
        if category.restaurant != self.request.user.restaurant:
            raise PermissionDenied("Invalid category.")
        serializer.save()

class TableViewSet(RestaurantScopedViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']

class OrderViewSet(RestaurantScopedViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']

    def perform_update(self, serializer):
        user = self.request.user
        if user.role in ['WAITER', 'KITCHEN']:
            if 'total_amount' in serializer.validated_data:
                raise PermissionDenied("You cannot modify the total amount.")
            
            new_status = serializer.validated_data.get('status')
            if new_status:
                if user.role == 'KITCHEN' and new_status not in ['open', 'preparing', 'served']:
                    raise PermissionDenied("Kitchen staff can only update preparation statuses.")
                if user.role == 'WAITER' and new_status == 'paid':
                    raise PermissionDenied("Waiters cannot collect payments.")
        super().perform_update(serializer)

class OrderItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RoleBasedAccess]
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    def get_queryset(self):
        if not self.request.user.restaurant:
            return self.queryset.none()
        return self.queryset.filter(order__restaurant=self.request.user.restaurant)
    def perform_create(self, serializer):
        order = serializer.validated_data.get('order')
        if order.restaurant != self.request.user.restaurant:
            raise PermissionDenied("Invalid order.")
        menu_item = serializer.validated_data.get('menu_item')
        price = serializer.validated_data.get('price_at_time', menu_item.price)
        
        user = self.request.user
        if user.role in ['WAITER', 'KITCHEN'] and 'price_at_time' in serializer.validated_data:
            if float(price) != float(menu_item.price):
                raise PermissionDenied("You cannot modify the item price.")
                
        serializer.save(price_at_time=price)

    def perform_update(self, serializer):
        user = self.request.user
        if user.role in ['WAITER', 'KITCHEN'] and 'price_at_time' in serializer.validated_data:
            if float(serializer.validated_data['price_at_time']) != float(serializer.instance.price_at_time):
                raise PermissionDenied("You cannot modify the item price.")
        super().perform_update(serializer)

class CustomerViewSet(RestaurantScopedViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER']
    write_roles = ['MANAGER', 'CASHIER']

class ExpenseViewSet(RestaurantScopedViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    read_roles = ['MANAGER']
    write_roles = ['MANAGER']

class DayCloseViewSet(RestaurantScopedViewSet):
    queryset = DayClose.objects.all()
    serializer_class = DayCloseSerializer
    read_roles = ['MANAGER']
    write_roles = ['MANAGER']

from django.contrib.auth import get_user_model
User = get_user_model()

class StaffViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RoleBasedAccess]
    read_roles = ['MANAGER']
    write_roles = ['MANAGER']
    
    def get_queryset(self):
        if not self.request.user.restaurant:
            return User.objects.none()
        return User.objects.filter(restaurant=self.request.user.restaurant).exclude(id=self.request.user.id)
        
    def get_serializer_class(self):
        if self.action == 'create':
            return StaffCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StaffUpdateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        role = serializer.validated_data['role']
        if role == 'OWNER' and self.request.user.role != 'OWNER':
            raise PermissionDenied("Only Owners can assign the OWNER role.")
            
        User.objects.create_user(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            email=serializer.validated_data.get('email', ''),
            role=role,
            restaurant=self.request.user.restaurant
        )

    def perform_update(self, serializer):
        target_user = serializer.instance
        user = self.request.user

        if target_user.role == 'OWNER' and user.role != 'OWNER':
            raise PermissionDenied("Cannot modify OWNER account.")

        if 'role' in serializer.validated_data and serializer.validated_data['role'] == 'OWNER' and user.role != 'OWNER':
            raise PermissionDenied("Only Owners can assign the OWNER role.")
            
        is_active_change = serializer.validated_data.get('is_active', target_user.is_active)
        if target_user.role == 'OWNER' and not is_active_change and target_user.is_active:
            active_owners = User.objects.filter(restaurant=target_user.restaurant, role='OWNER', is_active=True).exclude(id=target_user.id)
            if not active_owners.exists():
                raise PermissionDenied("Cannot deactivate the last active Owner.")

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Deactivate staff instead of deleting."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['post'])
    def assign_existing(self, request):
        username = request.data.get('username')
        role = request.data.get('role')
        if not username or not role:
            return Response({"detail": "Username and role required."}, status=status.HTTP_400_BAD_REQUEST)
        if role == 'OWNER' and request.user.role != 'OWNER':
            raise PermissionDenied("Cannot assign OWNER role.")
        if role not in ['OWNER', 'MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']:
            return Response({"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)
            
        from django.db import transaction
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(username=username)
                
                if user.restaurant:
                    return Response({"detail": "User is already assigned to a restaurant."}, status=status.HTTP_400_BAD_REQUEST)
                    
                user.restaurant = request.user.restaurant
                user.role = role
                user.save()
                return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

