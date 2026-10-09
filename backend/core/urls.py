from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ZoneViewSet, ReservationViewSet, SignupView, LoginView, LogoutView, MeView, CSRFTokenView, RestaurantOnboardingView, CategoryViewSet, MenuItemViewSet, MenuItemPriceHistoryViewSet, TableViewSet, OrderViewSet, OrderItemViewSet, CustomerViewSet, ExpenseViewSet, DayCloseViewSet, StaffViewSet, LayoutObjectViewSet, LoyaltySettingsViewSet, PointTransactionViewSet

urlpatterns = [
    path('csrf/', CSRFTokenView.as_view(), name='csrf'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('restaurant/onboarding/', RestaurantOnboardingView.as_view(), name='restaurant_onboarding'),
]

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menu-item')
router.register(r'menu-item-price-history', MenuItemPriceHistoryViewSet, basename='menu-item-price-history')
router.register(r'tables', TableViewSet, basename='table')
router.register(r'zones', ZoneViewSet, basename='zone')
router.register(r'layout-objects', LayoutObjectViewSet, basename='layout-object')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'day-close', DayCloseViewSet, basename='day-close')
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'loyalty-settings', LoyaltySettingsViewSet, basename='loyalty-settings')
router.register(r'point-transactions', PointTransactionViewSet, basename='point-transaction')

urlpatterns += router.urls

