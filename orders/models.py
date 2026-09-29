import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from products.models import Product


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('KHALTI', 'Khalti Sandbox'),
        ('COUNTER', 'Pay at Counter'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready for Pickup'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=32, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    customer_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True, help_text="Special instructions e.g. extra sugar, oat milk")
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    points_redeemed = models.PositiveIntegerField(default=0)
    points_earned = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COUNTER')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['order_status']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_prefix = timezone.now().strftime('%Y%m%d')
            unique_suffix = uuid.uuid4().hex[:6].upper()
            self.order_number = f"MCS-{date_prefix}-{unique_suffix}"
        super().save(*args, **kwargs)

    @property
    def status_color_class(self):
        colors = {
            'PENDING': 'bg-amber-100 text-amber-800 border-amber-300',
            'CONFIRMED': 'bg-blue-100 text-blue-800 border-blue-300',
            'PREPARING': 'bg-purple-100 text-purple-800 border-purple-300',
            'READY': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'COMPLETED': 'bg-stone-100 text-stone-800 border-stone-300',
            'CANCELLED': 'bg-rose-100 text-rose-800 border-rose-300',
        }
        return colors.get(self.order_status, 'bg-stone-100 text-stone-700 border-stone-200')

    @property
    def payment_badge_class(self):
        colors = {
            'PAID': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'PENDING': 'bg-amber-100 text-amber-800 border-amber-300',
            'FAILED': 'bg-rose-100 text-rose-800 border-rose-300',
            'REFUNDED': 'bg-gray-100 text-gray-800 border-gray-300',
        }
        return colors.get(self.payment_status, 'bg-stone-100 text-stone-700 border-stone-200')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.quantity}x {self.product.name} ({self.order.order_number})"

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)
