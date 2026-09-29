from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from orders.models import Order


class LoyaltyPointTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('EARNED', 'Earned from Purchase'),
        ('REDEEMED', 'Redeemed for Discount'),
        ('BONUS', 'Welcome / Promotional Bonus'),
        ('REFUNDED', 'Refund / Order Cancelled'),
        ('ADJUSTMENT', 'Staff / Admin Adjustment'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_transactions')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='loyalty_transactions')
    points = models.IntegerField(help_text="Positive for earned/bonus, negative for redeemed")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        sign = "+" if self.points > 0 else ""
        return f"{self.customer.username}: {sign}{self.points} pts ({self.get_transaction_type_display()})"

    @classmethod
    def get_user_balance(cls, user):
        """
        Calculate the current available points balance for a user.
        """
        if not user.is_authenticated:
            return 0
        total = cls.objects.filter(customer=user).aggregate(total=Sum('points'))['total']
        return total if total is not None else 0

    @classmethod
    def get_total_earned(cls, user):
        """
        Calculate total lifetime points earned by a user.
        """
        if not user.is_authenticated:
            return 0
        total = cls.objects.filter(customer=user, points__gt=0).aggregate(total=Sum('points'))['total']
        return total if total is not None else 0

    @classmethod
    def get_total_redeemed(cls, user):
        """
        Calculate total points redeemed by a user.
        """
        if not user.is_authenticated:
            return 0
        total = cls.objects.filter(customer=user, points__lt=0).aggregate(total=Sum('points'))['total']
        return abs(total) if total is not None else 0
