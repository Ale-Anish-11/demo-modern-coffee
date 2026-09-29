from .models import LoyaltyPointTransaction


def loyalty_context(request):
    """
    Context processor to make the current user's loyalty points available in templates.
    """
    if request.user.is_authenticated:
        points = LoyaltyPointTransaction.get_user_balance(request.user)
    else:
        points = 0
    return {
        'user_loyalty_points': points
    }
