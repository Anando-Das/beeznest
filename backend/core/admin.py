from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Restaurant

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Restaurant Details', {'fields': ('restaurant', 'role')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Restaurant)
