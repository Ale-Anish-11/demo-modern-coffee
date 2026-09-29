from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'total_amount', 'payment_method', 'payment_status', 'order_status', 'created_at')
    list_filter = ('order_status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'customer_name', 'email', 'phone')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')
