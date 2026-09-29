from django.contrib import admin
from .models import LoyaltyPointTransaction


@admin.register(LoyaltyPointTransaction)
class LoyaltyPointTransactionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'points', 'transaction_type', 'order', 'description', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('customer__username', 'customer__email', 'description')
