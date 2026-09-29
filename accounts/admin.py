from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import CustomerProfile


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Customer Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (CustomerProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_phone', 'is_staff', 'date_joined')

    def get_phone(self, instance):
        return getattr(instance, 'profile', None) and instance.profile.phone or '-'
    get_phone.short_description = 'Phone'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
