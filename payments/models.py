from django.db import models
from orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid / Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled by User'),
        ('REFUNDED', 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=50) # 'KHALTI' or 'COUNTER'
    transaction_id = models.CharField(max_length=150, blank=True, null=True, help_text="Khalti pidx or Transaction ID")
    reference_id = models.CharField(max_length=150, blank=True, null=True, help_text="Bank / Khalti txnId or counter receipt reference")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Payment #{self.id} for Order #{self.order.order_number} - {self.status}"
