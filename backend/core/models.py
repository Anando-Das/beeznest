from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True, help_text="Restaurant website URL")
    website_enabled = models.BooleanField(default=False, help_text="Whether the restaurant website is enabled/published")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('MANAGER', 'Manager'),
        ('CASHIER', 'Cashier'),
        ('WAITER', 'Waiter'),
        ('KITCHEN', 'Kitchen'),
    ]
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.username} - {self.role or 'No Role'}"

class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class MenuItemPriceHistory(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='price_history')
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.menu_item.name}: {self.old_price} -> {self.new_price}"


class Zone(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Table(models.Model):
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
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.seats} seats)"

class LayoutObject(models.Model):
    OBJECT_TYPE_CHOICES = [
        ('CASH_COUNTER', 'Cash Counter'),
        ('WINDOW', 'Window'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='layout_objects')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='layout_objects')
    object_type = models.CharField(max_length=20, choices=OBJECT_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_object_type_display()})"

class Order(models.Model):
    TYPE_CHOICES = [
        ('dine-in', 'Dine-in'),
        ('takeaway', 'Takeaway'),
        ('delivery', 'Delivery'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('preparing', 'Preparing'),
        ('served', 'Served'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='dine-in')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('other', 'Other'),
    ]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    processed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='processed_payments')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.amount}"

class Customer(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # Virtual columns for duplicate prevention (added via migration)
    # These are managed at database level for MariaDB 10.4 compatibility

    def __str__(self):
        return self.name

class Expense(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.category}: {self.amount}"

class DayClose(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='day_closes')
    date = models.DateField(auto_now_add=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cash_in_drawer = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expected_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Day Close {self.date}"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('RESERVED', 'Reserved'),
        ('CHECKED_IN', 'Checked In'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
        ('CANCELLED', 'Cancelled'),
    ]
    ACTIVE_STATUSES = ('RESERVED', 'CHECKED_IN')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reservations')
    customer_name = models.CharField(max_length=255)
    customer_contact = models.CharField(max_length=255, blank=True, null=True)
    table = models.ForeignKey(Table, on_delete=models.PROTECT, related_name='reservations')
    reservation_date = models.DateField()
    start_time = models.TimeField()
    expected_duration_minutes = models.IntegerField(default=120)
    guests = models.IntegerField(default=2)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RESERVED')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_reservations')
    updated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_reservations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['table', 'reservation_date', 'status']),
            models.Index(fields=['restaurant', 'reservation_date']),
            models.Index(fields=['restaurant', 'status']),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.table.name} at {self.reservation_date} {self.start_time}"

    @property
    def guest_count(self):
        return self.guests

    def start_datetime(self):
        import datetime
        return datetime.datetime.combine(self.reservation_date, self.start_time)

    def end_datetime(self):
        import datetime
        return self.start_datetime() + datetime.timedelta(minutes=self.expected_duration_minutes)


class ReservationHistory(models.Model):
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('EDITED', 'Edited'),
        ('TABLE_CHANGED', 'Table changed'),
        ('CHECKED_IN', 'Checked in'),
        ('NO_SHOW', 'No show'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('CORRECTED', 'Corrected'),
    ]
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    previous_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    performed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservation_actions')
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on reservation {self.reservation_id}"


class LoyaltySettings(models.Model):
    """Restaurant-specific loyalty program settings."""
    restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='loyalty_settings')
    enabled = models.BooleanField(default=False)
    points_earning_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.00,
        help_text="Amount of purchase (in currency) required to earn 1 point"
    )
    points_redemption_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1.00,
        help_text="Currency value of 1 point when redeeming"
    )
    points_expiry_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of days before points expire. Null means no expiry."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loyalty Settings for {self.restaurant.name}"


class PointTransaction(models.Model):
    """Track all point transactions for audit and balance history."""
    TRANSACTION_TYPE_CHOICES = [
        ('EARNED', 'Earned'),
        ('REDEEMED', 'Redeemed'),
        ('EXPIRED', 'Expired'),
        ('REVERSED', 'Reversed'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='point_transactions')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='point_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField(help_text="Positive for earned, negative for redeemed/reversed")
    balance_after = models.IntegerField(help_text="Customer balance after this transaction")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='point_transactions')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='point_transactions')
    description = models.TextField(blank=True)
    related_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reversals', help_text="Reference to original transaction if this is a reversal")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When these points will expire (for earned points)")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['restaurant', 'created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.transaction_type}: {self.points} points for {self.customer.name}"


class WebsiteRequest(models.Model):
    """Website request from a restaurant for website creation."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='website_requests')
    website_name = models.CharField(max_length=255, help_text="Name for the website")
    description = models.TextField(blank=True, null=True, help_text="Description of the website requirements")
    logo = models.ImageField(upload_to='website_requests/logos/', blank=True, null=True, help_text="Restaurant logo")
    colours = models.JSONField(default=list, blank=True, help_text="List of hex colour codes for website theme")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Website Request for {self.restaurant.name} - {self.status}"


class WebsiteRequestPhoto(models.Model):
    """Photos attached to a website request."""
    website_request = models.ForeignKey(WebsiteRequest, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='website_requests/photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Photo for request {self.website_request.id}"
