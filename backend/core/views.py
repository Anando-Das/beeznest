from rest_framework import status, views, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from .serializers import SignupSerializer, LoginSerializer, UserSerializer, RestaurantSerializer, WebsiteRequestCreateSerializer, WebsiteRequestSerializer
from .models import Restaurant, WebsiteRequest

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

class WebsiteStatusView(views.APIView):
    """API endpoint to get website status for the authenticated user's restaurant."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.restaurant:
            return Response({"detail": "You must belong to a restaurant."}, status=status.HTTP_400_BAD_REQUEST)

        restaurant = request.user.restaurant
        return Response({
            "has_website": restaurant.website_enabled,
            "website_url": restaurant.website_url
        }, status=status.HTTP_200_OK)


class WebsiteRequestView(views.APIView):
    """API endpoint for submitting and retrieving website requests."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get(self, request):
        """Get the current restaurant's website request status."""
        if not request.user.restaurant:
            return Response({"detail": "You must belong to a restaurant."}, status=status.HTTP_400_BAD_REQUEST)

        restaurant = request.user.restaurant
        # Get the most recent request
        request_obj = WebsiteRequest.objects.filter(restaurant=restaurant).order_by('-created_at').first()

        if not request_obj:
            return Response({
                "has_request": False,
                "request": None
            }, status=status.HTTP_200_OK)

        serializer = WebsiteRequestSerializer(request_obj)
        return Response({
            "has_request": True,
            "request": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Submit a new website request."""
        if not request.user.restaurant:
            return Response({"detail": "You must belong to a restaurant."}, status=status.HTTP_400_BAD_REQUEST)

        restaurant = request.user.restaurant

        # Check for existing active requests (PENDING or IN_PROGRESS)
        active_request = WebsiteRequest.objects.filter(
            restaurant=restaurant,
            status__in=['PENDING', 'IN_PROGRESS']
        ).exists()

        if active_request:
            return Response(
                {"detail": "You already have an active website request. Please wait for it to be processed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = WebsiteRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # Create the website request
            website_request = WebsiteRequest.objects.create(
                restaurant=restaurant,
                website_name=serializer.validated_data['website_name'],
                description=serializer.validated_data.get('description', ''),
                logo=serializer.validated_data.get('logo'),
                colours=serializer.validated_data.get('colours', []),
                status='PENDING'
            )

            # Create photo records
            from .models import WebsiteRequestPhoto
            for photo in serializer.validated_data['photos']:
                WebsiteRequestPhoto.objects.create(
                    website_request=website_request,
                    photo=photo
                )

        response_serializer = WebsiteRequestSerializer(website_request)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from .models import Category, MenuItem, MenuItemPriceHistory, Table, Order, OrderItem, Customer, Expense, DayClose, Zone, Reservation, LayoutObject, LoyaltySettings, PointTransaction
from .serializers import CategorySerializer, MenuItemSerializer, MenuItemPriceHistorySerializer, TableSerializer, OrderSerializer, OrderItemSerializer, OrderCreateSerializer, OrderUpdateSerializer, CustomerSerializer, CustomerSearchSerializer, CustomerOrderHistorySummarySerializer, ExpenseSerializer, DayCloseSerializer, StaffCreateSerializer, StaffUpdateSerializer, ZoneSerializer, ReservationSerializer, ReservationHistorySerializer, LayoutObjectSerializer, LoyaltySettingsSerializer, PointTransactionSerializer, PointRedemptionSerializer
from .permissions import RoleBasedAccess, IsOwnerOnly
from rest_framework.decorators import action
from . import reservation_service as reservation_svc

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
    write_roles = ['MANAGER', 'KITCHEN']
    def get_queryset(self):
        if not self.request.user.restaurant:
            return self.queryset.none()
        return self.queryset.filter(category__restaurant=self.request.user.restaurant)
    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'KITCHEN':
            raise PermissionDenied("Kitchen staff cannot create menu items.")
        category = serializer.validated_data.get('category')
        if category.restaurant != self.request.user.restaurant:
            raise PermissionDenied("Invalid category.")
        serializer.save()
    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance
        if user.role == 'KITCHEN':
            # Kitchen can ONLY change is_available
            allowed_fields = {'is_available'}
            updated_fields = set(serializer.validated_data.keys())
            if not updated_fields.issubset(allowed_fields):
                raise PermissionDenied("Kitchen staff can only change availability.")
        
        old_price = instance.price
        new_price = serializer.validated_data.get('price', instance.price)
        if old_price != new_price:
            if user.role not in ['OWNER', 'MANAGER']:
                raise PermissionDenied("Only Owners and Managers can change prices.")
        
        updated_instance = serializer.save()
        if old_price != updated_instance.price:
            MenuItemPriceHistory.objects.create(
                menu_item=updated_instance,
                old_price=old_price,
                new_price=updated_instance.price,
                changed_by=user
            )
    def perform_destroy(self, instance):
        if self.request.user.role == 'KITCHEN':
            raise PermissionDenied("Kitchen staff cannot delete menu items.")
        instance.delete()

class MenuItemPriceHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RoleBasedAccess]
    queryset = MenuItemPriceHistory.objects.all()
    serializer_class = MenuItemPriceHistorySerializer
    read_roles = ['MANAGER']
    write_roles = ['MANAGER']
    def get_queryset(self):
        if not self.request.user.restaurant:
            return self.queryset.none()
        return self.queryset.filter(menu_item__category__restaurant=self.request.user.restaurant)
    def perform_update(self, serializer):
        # Do not allow modifying history such that it affects orders
        serializer.save()


class TableViewSet(RestaurantScopedViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']

    def get_queryset(self):
        today = timezone.localdate()
        return super().get_queryset().select_related('zone').prefetch_related(
            Prefetch(
                'reservations',
                queryset=Reservation.objects.filter(
                    reservation_date=today,
                    status__in=['RESERVED', 'CHECKED_IN'],
                ).order_by('start_time'),
                to_attr='todays_active_reservations',
            )
        )

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


class OrderViewSet(RestaurantScopedViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']

    def get_queryset(self):
        qs = super().get_queryset()
        
        status = self.request.query_params.get('status')
        order_type = self.request.query_params.get('order_type')
        
        if status:
            status_list = [s.strip() for s in status.split(',')]
            qs = qs.filter(status__in=status_list)
            
        if order_type:
            qs = qs.filter(order_type=order_type)
            
        return qs

    def perform_update(self, serializer):
        user = self.request.user
        if user.role in ['WAITER', 'KITCHEN']:
            if 'total_amount' in serializer.validated_data:
                raise PermissionDenied("You cannot modify the total amount.")
            
            new_status = serializer.validated_data.get('status')
            if new_status:
                if user.role == 'KITCHEN' and new_status not in ['open', 'preparing', 'served']:
                    raise PermissionDenied("Kitchen staff can only update preparation statuses.")
                if new_status == 'paid':
                    raise PermissionDenied("Payments must be processed through the dedicated payment endpoint.")
                    
        # Also block direct payment status for managers/owners via standard update
        if serializer.validated_data.get('status') == 'paid':
            raise PermissionDenied("Payments must be processed through the dedicated payment endpoint.")
        super().perform_update(serializer)

    @action(detail=False, methods=['post'])
    def create_with_items(self, request):
        """Atomic order creation with items in a single transaction."""
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        from . import reservation_service
        
        user = request.user
        restaurant = user.restaurant
        table = serializer.validated_data.get('table')
        items_data = serializer.validated_data['items']
        customer = serializer.validated_data.get('customer')  # May be set by serializer if customer_id provided
        customer_phone = serializer.validated_data.get('customer_phone')
        customer_name = serializer.validated_data.get('customer_name')
        customer_email = serializer.validated_data.get('customer_email')

        with transaction.atomic():
            # Lock table if present to prevent race conditions
            if table:
                table = reservation_service.lock_table(table.pk)
                serializer.validated_data['table'] = table

            # If customer not already set by customer_id, handle phone-based lookup/creation
            if not customer and customer_phone:
                # Normalize phone (already done in serializer validation)
                normalized_phone = customer_phone.strip()

                # Try to get existing customer by restaurant and phone
                customer = Customer.objects.filter(
                    restaurant=restaurant,
                    phone=normalized_phone
                ).first()

                if customer:
                    # Update existing customer only if non-blank values provided
                    if customer_name and customer_name.strip():
                        customer.name = customer_name.strip()
                    if customer_email and customer_email.strip():
                        customer.email = customer_email.strip().lower()
                    customer.save()
                else:
                    # Create new customer with provided name/email or defaults
                    customer = Customer.objects.create(
                        restaurant=restaurant,
                        phone=normalized_phone,
                        name=customer_name.strip() if customer_name and customer_name.strip() else 'Guest',
                        email=customer_email.strip().lower() if customer_email and customer_email.strip() else None
                    )
            
            # Calculate total amount from validated menu item prices
            total_amount = 0
            for item_data in items_data:
                menu_item = item_data['menu_item']
                quantity = item_data['quantity']
                total_amount += menu_item.price * quantity
            
            # Create order with calculated total
            order = Order.objects.create(
                restaurant=restaurant,
                customer=customer,
                table=table,
                order_type=serializer.validated_data.get('order_type', 'dine-in'),
                status=serializer.validated_data.get('status', 'open'),
                total_amount=total_amount
            )
            
            # Create order items with price snapshots
            for item_data in items_data:
                OrderItem.objects.create(
                    order=order,
                    menu_item=item_data['menu_item'],
                    quantity=item_data['quantity'],
                    price_at_time=item_data['menu_item'].price,
                    notes=item_data.get('notes')
                )
            
            # Sync table status - mark as occupied if order is dine-in and has table
            if table and order.order_type == 'dine-in':
                reservation_service.sync_table_status_for_orders(table)
        
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def update_with_items(self, request, pk=None):
        """Atomic order update with items in a single transaction."""
        order = self.get_object()
        
        # Prevent editing paid or cancelled orders
        if order.status in ['paid', 'cancelled']:
            return Response(
                {"detail": f"Cannot modify an order that is {order.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OrderUpdateSerializer(order, data=request.data, context={'request': request}, partial=True)
        serializer.is_valid(raise_exception=True)
        
        from . import reservation_service
        
        items_data = serializer.validated_data.get('items')
        status_change = serializer.validated_data.get('status')
        
        with transaction.atomic():
            # Lock table if present to prevent race conditions
            table = order.table
            if table:
                table = reservation_service.lock_table(table.pk)
            
            # Handle item updates
            if items_data is not None:
                # Build a map of existing menu_item_id to price_at_time to preserve original prices
                existing_prices = {item.menu_item_id: item.price_at_time for item in order.items.all()}
                
                # Delete existing items
                order.items.all().delete()
                
                # Recreate items, preserving price for existing menu items, using current price for new ones
                total_amount = 0
                for item_data in items_data:
                    menu_item = item_data['menu_item']
                    quantity = item_data['quantity']
                    
                    # Use original price if menu_item was in the order, else current menu price
                    item_price = existing_prices.get(menu_item.id, menu_item.price)
                    total_amount += item_price * quantity
                    
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantity,
                        price_at_time=item_price,
                        notes=item_data.get('notes')
                    )
                
                # Update total amount
                order.total_amount = total_amount
            
            # Handle status change if provided
            if status_change:
                order.status = status_change
            
            order.save()
            
            # Sync table status if order has table and is dine-in
            if table and order.order_type == 'dine-in':
                reservation_service.sync_table_status_for_orders(table)
        
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pay(self, request, pk=None):
        """Process payment for an order and award loyalty points if enabled."""
        user = request.user
        if user.role not in ['OWNER', 'MANAGER', 'CASHIER']:
            raise PermissionDenied("You do not have permission to process payments.")

        method = request.data.get('method', 'cash')
        if method not in ['cash', 'card', 'bkash', 'nagad', 'other']:
            return Response({"detail": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Lock the order to prevent concurrent payment processing
            try:
                order = Order.objects.select_for_update().get(pk=pk, restaurant=user.restaurant)
            except Order.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

            if order.status in ['paid', 'cancelled']:
                return Response(
                    {"detail": f"Cannot pay an order that is {order.status}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            from .models import Payment
            payment = Payment.objects.create(
                order=order,
                amount=order.total_amount,
                method=method,
                processed_by=user
            )

            order.status = 'paid'
            order.save()

            # Award loyalty points if enabled and order has a customer
            if order.customer:
                try:
                    loyalty_settings = LoyaltySettings.objects.get(restaurant=user.restaurant)
                    if loyalty_settings.enabled and order.customer:
                        # Check if points already awarded for this payment (idempotency)
                        existing_award = PointTransaction.objects.filter(
                            payment=payment,
                            transaction_type='EARNED'
                        ).exists()

                        if not existing_award:
                            # Calculate points to award
                            points_to_award = int(order.total_amount / loyalty_settings.points_earning_rate)

                            if points_to_award > 0:
                                # Lock customer for update
                                customer = Customer.objects.select_for_update().get(pk=order.customer.id)
                                new_balance = customer.points + points_to_award
                                customer.points = new_balance
                                customer.save()

                                # Calculate expiry date if configured
                                expires_at = None
                                if loyalty_settings.points_expiry_days:
                                    from datetime import timedelta
                                    expires_at = timezone.now() + timedelta(days=loyalty_settings.points_expiry_days)

                                # Create transaction record
                                PointTransaction.objects.create(
                                    customer=customer,
                                    restaurant=user.restaurant,
                                    transaction_type='EARNED',
                                    points=points_to_award,
                                    balance_after=new_balance,
                                    order=order,
                                    payment=payment,
                                    description=f"Earned {points_to_award} points from order #{order.id}",
                                    expires_at=expires_at
                                )
                except LoyaltySettings.DoesNotExist:
                    # Loyalty settings not configured, skip point awarding
                    pass

            # Sync table status if order has table and is dine-in
            if order.table and order.order_type == 'dine-in':
                from . import reservation_service
                reservation_service.sync_table_status_for_orders(order.table)

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order with proper validation, table status sync, and point reversal."""
        order = self.get_object()

        # Prevent cancelling paid orders
        if order.status == 'paid':
            return Response(
                {"detail": "Cannot cancel a paid order."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent re-cancelling
        if order.status == 'cancelled':
            return Response(
                {"detail": "Order is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from . import reservation_service

        with transaction.atomic():
            # Lock table if present
            table = order.table
            if table:
                table = reservation_service.lock_table(table.pk)

            # Cancel the order
            order.status = 'cancelled'
            order.save()

            # Reverse loyalty points if any were earned for this order
            if order.customer:
                earned_transactions = PointTransaction.objects.filter(
                    order=order,
                    transaction_type='EARNED'
                )

                for earned_tx in earned_transactions:
                    # Check if already reversed
                    existing_reversal = PointTransaction.objects.filter(
                        related_transaction=earned_tx,
                        transaction_type='REVERSED'
                    ).exists()

                    if not existing_reversal:
                        # Lock customer for update
                        customer = Customer.objects.select_for_update().get(pk=order.customer.id)
                        new_balance = customer.points - earned_tx.points
                        customer.points = max(0, new_balance)  # Prevent negative balance
                        customer.save()

                        # Create reversal transaction
                        PointTransaction.objects.create(
                            customer=customer,
                            restaurant=order.restaurant,
                            transaction_type='REVERSED',
                            points=-earned_tx.points,
                            balance_after=customer.points,
                            order=order,
                            related_transaction=earned_tx,
                            description=f"Reversed points from cancelled order #{order.id}"
                        )

            # Sync table status - may free the table if no other active orders
            if table and order.order_type == 'dine-in':
                reservation_service.sync_table_status_for_orders(table)

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

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
        if not menu_item.is_available:
            raise serializers.ValidationError({"menu_item": "This item is currently inactive and cannot be ordered."})
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

    def create(self, request, *args, **kwargs):
        """Override create to handle database integrity errors gracefully."""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            # Check for unique constraint violation
            error_msg = str(e).lower()
            if 'customer_restaurant_phone_unique' in error_msg or 'phone' in error_msg:
                return Response(
                    {"detail": "A customer with this phone number already exists in your restaurant."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'customer_restaurant_email_unique' in error_msg or 'email' in error_msg:
                return Response(
                    {"detail": "A customer with this email address already exists in your restaurant."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise

    def update(self, request, *args, **kwargs):
        """Override update to handle database integrity errors gracefully."""
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            # Check for unique constraint violation
            error_msg = str(e).lower()
            if 'customer_restaurant_phone_unique' in error_msg or 'phone' in error_msg:
                return Response(
                    {"detail": "A customer with this phone number already exists in your restaurant."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'customer_restaurant_email_unique' in error_msg or 'email' in error_msg:
                return Response(
                    {"detail": "A customer with this email address already exists in your restaurant."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search customers by phone number or email within the authenticated user's restaurant.
        Query parameters:
            - phone: partial or full phone number (whitespace-normalized)
            - email: partial or full email address (case-insensitive, whitespace-normalized)
        Returns up to 10 results with minimal fields for POS autocomplete.
        """
        phone = request.query_params.get('phone', '').strip()
        email = request.query_params.get('email', '').strip().lower()

        # Require at least one search parameter with minimum length
        if not phone and not email:
            return Response(
                {"detail": "At least one search parameter (phone or email) is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Enforce minimum query length to prevent overly broad searches
        if phone and len(phone) < 3:
            return Response(
                {"detail": "Phone search requires at least 3 characters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if email and len(email) < 3:
            return Response(
                {"detail": "Email search requires at least 3 characters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build queryset scoped to user's restaurant
        queryset = self.get_queryset()

        # Apply phone filter (partial match, whitespace-normalized)
        if phone:
            queryset = queryset.filter(phone__icontains=phone)

        # Apply email filter (partial match, case-insensitive)
        if email:
            queryset = queryset.filter(email__icontains=email)

        # Limit results for autocomplete performance
        queryset = queryset[:10]

        # Serialize with lightweight serializer
        serializer = CustomerSearchSerializer(queryset, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def order_history(self, request, pk=None):
        """
        Retrieve order history for a specific customer.
        Returns:
            - Customer basic information
            - Total order count
            - Total spending (sum of paid order amounts)
            - Most recent order date
            - List of all orders with items and payment details
        """
        customer = self.get_object()

        # Use annotate to calculate aggregates in a single query
        from django.db.models import Sum, Max, Count, Q

        orders_qs = customer.orders.all()

        # Calculate statistics
        stats = orders_qs.aggregate(
            total_orders=Count('id'),
            total_spending=Sum('total_amount', filter=Q(status='paid')),
            most_recent_order_date=Max('created_at')
        )

        # Prepare the response data
        response_data = {
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'points': customer.points,
            'created_at': customer.created_at,
            'total_orders': stats['total_orders'] or 0,
            'total_spending': stats['total_spending'] or 0,
            'most_recent_order_date': stats['most_recent_order_date'],
            'orders': []
        }

        # Fetch orders with related data (avoid N+1 queries)
        # Don't select_related payment since it's optional OneToOneField
        orders_with_items = orders_qs.select_related(
            'table'
        ).prefetch_related(
            'items__menu_item'
        ).order_by('-created_at')

        # Serialize orders
        for order in orders_with_items:
            # Safely get payment using getattr with default
            payment = getattr(order, 'payment', None)

            order_data = {
                'id': order.id,
                'order_type': order.order_type,
                'status': order.status,
                'total_amount': order.total_amount,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'table_name': order.table.name if order.table else None,
                'items': [
                    {
                        'menu_item_name': item.menu_item.name,
                        'quantity': item.quantity,
                        'price_at_time': item.price_at_time,
                        'notes': item.notes
                    }
                    for item in order.items.all()
                ],
                'payment_method': payment.method if payment else None,
                'payment_amount': payment.amount if payment else None,
                'payment_timestamp': payment.timestamp if payment else None
            }
            response_data['orders'].append(order_data)

        return Response(response_data)

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


class ZoneViewSet(RestaurantScopedViewSet):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']

class LayoutObjectViewSet(RestaurantScopedViewSet):
    queryset = LayoutObject.objects.all()
    serializer_class = LayoutObjectSerializer
    read_roles = ['MANAGER', 'CASHIER', 'WAITER', 'KITCHEN']
    write_roles = ['MANAGER']

class ReservationViewSet(RestaurantScopedViewSet):
    queryset = Reservation.objects.all().select_related(
        'table', 'table__zone', 'created_by', 'updated_by'
    )
    serializer_class = ReservationSerializer
    read_roles = ['MANAGER', 'WAITER', 'CASHIER']
    write_roles = ['MANAGER', 'WAITER']

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        reservation_date = params.get('reservation_date')
        status_filter = params.get('status')
        table_id = params.get('table')
        customer_name = params.get('customer_name')
        customer_contact = params.get('customer_contact')
        search = params.get('search')
        if reservation_date:
            qs = qs.filter(reservation_date=reservation_date)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if table_id:
            qs = qs.filter(table_id=table_id)
        if customer_name:
            qs = qs.filter(customer_name__icontains=customer_name)
        if customer_contact:
            qs = qs.filter(customer_contact__icontains=customer_contact)
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(customer_name__icontains=search) | Q(customer_contact__icontains=search))
        return qs.order_by('reservation_date', 'start_time', 'id')

    def perform_create(self, serializer):
        if not self.request.user.restaurant:
            raise PermissionDenied("You must belong to a restaurant to perform this action.")
        serializer.save(
            restaurant=self.request.user.restaurant,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Reservations cannot be deleted. Cancel or complete them instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def _transition(self, request, new_status, allow_correction=False):
        reservation = self.get_object()
        reason = request.data.get('reason')
        with transaction.atomic():
            reservation_svc.lock_table(reservation.table_id)
            locked = Reservation.objects.select_for_update().get(pk=reservation.pk)
            updated = reservation_svc.apply_status_transition(
                locked,
                new_status,
                request.user,
                reason=reason,
                allow_correction=allow_correction,
            )
        return Response(ReservationSerializer(updated, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='check-in')
    def check_in(self, request, pk=None):
        return self._transition(request, 'CHECKED_IN')

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        return self._transition(request, 'CANCELLED')

    @action(detail=True, methods=['post'], url_path='no-show')
    def no_show(self, request, pk=None):
        return self._transition(request, 'NO_SHOW')

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        return self._transition(request, 'COMPLETED')

    @action(detail=True, methods=['post'], url_path='correct')
    def correct(self, request, pk=None):
        if request.user.role not in ['OWNER', 'MANAGER']:
            raise PermissionDenied("Only owners and managers can correct reservation status.")
        new_status = request.data.get('status')
        if new_status not in dict(Reservation.STATUS_CHOICES):
            return Response({'status': ['Invalid status.']}, status=status.HTTP_400_BAD_REQUEST)
        return self._transition(request, new_status, allow_correction=True)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        reservation = self.get_object()
        items = reservation.history.select_related('performed_by').all()
        return Response(ReservationHistorySerializer(items, many=True).data)


class LoyaltySettingsViewSet(RestaurantScopedViewSet):
    queryset = LoyaltySettings.objects.all()
    serializer_class = LoyaltySettingsSerializer
    read_roles = ['OWNER', 'MANAGER', 'CASHIER', 'WAITER']
    write_roles = ['OWNER', 'MANAGER']

    def get_queryset(self):
        """Override to return only the restaurant's settings."""
        restaurant = self.request.user.restaurant
        if not restaurant:
            return LoyaltySettings.objects.none()
        return LoyaltySettings.objects.filter(restaurant=restaurant)

    def get_object(self):
        """Get or create loyalty settings for the restaurant."""
        restaurant = self.request.user.restaurant
        if not restaurant:
            raise PermissionDenied("You must belong to a restaurant.")

        obj, created = LoyaltySettings.objects.get_or_create(
            restaurant=restaurant,
            defaults={
                'enabled': False,
                'points_earning_rate': 100.00,
                'points_redemption_rate': 1.00,
                'points_expiry_days': None
            }
        )
        return obj

    @action(detail=False, methods=['get'])
    def my_settings(self, request):
        """Get the restaurant's loyalty settings (convenience endpoint)."""
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class PointTransactionViewSet(RestaurantScopedViewSet):
    queryset = PointTransaction.objects.all()
    serializer_class = PointTransactionSerializer
    read_roles = ['OWNER', 'MANAGER', 'CASHIER', 'WAITER']
    write_roles = []  # Transactions are created programmatically, not via API

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs

    @action(detail=False, methods=['post'])
    def redeem(self, request):
        """Redeem points for a discount on an order. Optionally process payment if payment_method is provided."""
        user = request.user
        if user.role not in ['OWNER', 'MANAGER', 'CASHIER']:
            raise PermissionDenied("You do not have permission to redeem points.")

        serializer = PointRedemptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        points_to_redeem = serializer.validated_data['points_to_redeem']
        order_id = serializer.validated_data['order_id']
        payment_method = serializer.validated_data.get('payment_method')

        restaurant = user.restaurant
        if not restaurant:
            raise PermissionDenied("You must belong to a restaurant.")

        # Get loyalty settings
        try:
            loyalty_settings = LoyaltySettings.objects.get(restaurant=restaurant)
        except LoyaltySettings.DoesNotExist:
            return Response(
                {"detail": "Loyalty program is not configured for this restaurant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not loyalty_settings.enabled:
            return Response(
                {"detail": "Loyalty program is not enabled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Lock order and customer for update
            try:
                order = Order.objects.select_for_update().get(
                    pk=order_id,
                    restaurant=restaurant
                )
            except Order.DoesNotExist:
                return Response(
                    {"detail": "Order not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not order.customer:
                return Response(
                    {"detail": "Order must have a customer to redeem points."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # If payment_method is provided, validate order can be paid
            if payment_method:
                if order.status in ['paid', 'cancelled']:
                    return Response(
                        {"detail": f"Cannot pay an order that is {order.status}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if payment_method not in ['cash', 'card', 'bkash', 'nagad', 'other']:
                    return Response(
                        {"detail": "Invalid payment method."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            customer = Customer.objects.select_for_update().get(pk=order.customer.id)

            # Check if points have already been redeemed for this order
            existing_redemption = PointTransaction.objects.filter(
                order=order,
                transaction_type='REDEEMED'
            ).exists()

            if existing_redemption:
                return Response(
                    {"detail": "Points have already been redeemed for this order."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate customer has enough points
            if customer.points < points_to_redeem:
                return Response(
                    {"detail": f"Insufficient points. Customer has {customer.points} points."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate discount
            discount_amount = points_to_redeem * loyalty_settings.points_redemption_rate

            # Update customer balance
            new_balance = customer.points - points_to_redeem
            customer.points = new_balance
            customer.save()

            # Create transaction record
            PointTransaction.objects.create(
                customer=customer,
                restaurant=restaurant,
                transaction_type='REDEEMED',
                points=-points_to_redeem,
                balance_after=new_balance,
                order=order,
                description=f"Redeemed {points_to_redeem} points for discount on order #{order.id}"
            )

            # Update order total
            order.total_amount = max(0, order.total_amount - discount_amount)
            order.save()

            # If payment_method is provided, process payment atomically
            if payment_method:
                from .models import Payment
                payment = Payment.objects.create(
                    order=order,
                    amount=order.total_amount,
                    method=payment_method,
                    processed_by=user
                )

                order.status = 'paid'
                order.save()

                # Award loyalty points if enabled and order has a customer
                # Note: Points are awarded based on the final amount after discount
                if order.customer:
                    try:
                        loyalty_settings_check = LoyaltySettings.objects.get(restaurant=user.restaurant)
                        if loyalty_settings_check.enabled and order.customer:
                            # Check if points already awarded for this payment (idempotency)
                            existing_award = PointTransaction.objects.filter(
                                payment=payment,
                                transaction_type='EARNED'
                            ).exists()

                            if not existing_award:
                                # Calculate points to award based on final amount
                                points_to_award = int(order.total_amount / loyalty_settings_check.points_earning_rate)

                                if points_to_award > 0:
                                    # Lock customer for update (already locked above)
                                    # Refresh customer balance
                                    customer.refresh_from_db()
                                    new_balance_after_earn = customer.points + points_to_award
                                    customer.points = new_balance_after_earn
                                    customer.save()

                                    # Calculate expiry date if configured
                                    expires_at = None
                                    if loyalty_settings_check.points_expiry_days:
                                        from datetime import timedelta
                                        expires_at = timezone.now() + timedelta(days=loyalty_settings_check.points_expiry_days)

                                    # Create transaction record
                                    PointTransaction.objects.create(
                                        customer=customer,
                                        restaurant=user.restaurant,
                                        transaction_type='EARNED',
                                        points=points_to_award,
                                        balance_after=new_balance_after_earn,
                                        order=order,
                                        payment=payment,
                                        description=f"Earned {points_to_award} points from order #{order.id}",
                                        expires_at=expires_at
                                    )
                    except LoyaltySettings.DoesNotExist:
                        # Loyalty settings not configured, skip point awarding
                        pass

                # Sync table status if order has table and is dine-in
                if order.table and order.order_type == 'dine-in':
                    from . import reservation_service
                    reservation_service.sync_table_status_for_orders(order.table)

                return Response({
                    "detail": "Points redeemed and payment processed successfully.",
                    "points_redeemed": points_to_redeem,
                    "discount_amount": float(discount_amount),
                    "customer_balance_after_redemption": new_balance,
                    "final_order_total": float(order.total_amount),
                    "payment_processed": True,
                    "payment_method": payment_method,
                    "order": OrderSerializer(order).data
                }, status=status.HTTP_200_OK)

        return Response({
            "detail": "Points redeemed successfully.",
            "points_redeemed": points_to_redeem,
            "discount_amount": float(discount_amount),
            "new_balance": new_balance,
            "customer_balance_after_redemption": new_balance,
            "new_order_total": float(order.total_amount),
            "final_order_total": float(order.total_amount),
            "payment_processed": False
        }, status=status.HTTP_200_OK)
