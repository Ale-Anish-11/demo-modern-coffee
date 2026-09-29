from decimal import Decimal
from django.conf import settings
from django.db import transaction
from .models import LoyaltyPointTransaction


def calculate_points_earned(amount):
    """
    Configurable points calculation.
    Default: Every Rs. 100 spent = 10 points (or settings.LOYALTY_POINTS_PER_HUNDRED).
    Example: Rs. 550 => (550 // 100) * 10 = 50 points.
    """
    if not amount or amount <= 0:
        return 0
    hundreds = int(Decimal(str(amount)) // Decimal('100'))
    rate = getattr(settings, 'LOYALTY_POINTS_PER_HUNDRED', 10)
    return hundreds * rate


def calculate_discount_for_points(points):
    """
    Calculate NPR discount for redeemed points.
    Example: 50 points * 1.0 = Rs. 50.00
    """
    if not points or points <= 0:
        return Decimal('0.00')
    redeem_rate = Decimal(str(getattr(settings, 'LOYALTY_POINT_REDEEM_VALUE', 1.0)))
    return Decimal(str(points)) * redeem_rate


@transaction.atomic
def award_points_for_order(order):
    """
    Awards loyalty points to the customer for an eligible order (if not already awarded).
    Called when order is paid or confirmed.
    """
    if not order.customer or order.total_amount <= 0:
        return 0

    # Prevent duplicate points award for the same order
    already_awarded = LoyaltyPointTransaction.objects.filter(
        customer=order.customer,
        order=order,
        transaction_type='EARNED'
    ).exists()

    if already_awarded:
        return 0

    points_to_award = calculate_points_earned(order.total_amount)
    if points_to_award > 0:
        LoyaltyPointTransaction.objects.create(
            customer=order.customer,
            order=order,
            points=points_to_award,
            transaction_type='EARNED',
            description=f"Earned from Order #{order.order_number} (Rs. {order.total_amount})"
        )
        order.points_earned = points_to_award
        order.save(update_fields=['points_earned'])
        return points_to_award
    return 0


@transaction.atomic
def redeem_points_for_order(order, points_to_redeem):
    """
    Deducts points for an order at checkout.
    Verifies user has enough balance securely on the backend.
    """
    if not order.customer or points_to_redeem <= 0:
        return Decimal('0.00')

    user_balance = LoyaltyPointTransaction.get_user_balance(order.customer)
    if points_to_redeem > user_balance:
        points_to_redeem = user_balance

    if points_to_redeem <= 0:
        return Decimal('0.00')

    discount_amount = calculate_discount_for_points(points_to_redeem)

    LoyaltyPointTransaction.objects.create(
        customer=order.customer,
        order=order,
        points=-points_to_redeem,
        transaction_type='REDEEMED',
        description=f"Redeemed for Rs. {discount_amount} discount on Order #{order.order_number}"
    )

    return discount_amount
