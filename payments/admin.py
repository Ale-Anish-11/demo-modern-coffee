from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'payment_method', 'amount', 'status', 'transaction_id', 'reference_id', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('order__order_number', 'transaction_id', 'reference_id')
    readonly_fields = ('created_at', 'updated_at')
