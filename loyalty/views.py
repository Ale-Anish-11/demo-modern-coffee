from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import LoyaltyPointTransaction
from django.conf import settings


@login_required
def rewards_dashboard_view(request):
    user = request.user
    balance = LoyaltyPointTransaction.get_user_balance(user)
    total_earned = LoyaltyPointTransaction.get_total_earned(user)
    total_redeemed = LoyaltyPointTransaction.get_total_redeemed(user)
    transactions = LoyaltyPointTransaction.objects.filter(customer=user).order_by('-created_at')

    # Available loyalty tiers / reward perks
    rate = getattr(settings, 'LOYALTY_POINTS_PER_HUNDRED', 10)
    perk_tiers = [
        {'name': 'Bronze Sip', 'min_points': 0, 'perk': 'Earn 10 points per Rs. 100 spent'},
        {'name': 'Silver Brew', 'min_points': 150, 'perk': 'Free syrup upgrade & birthday treat'},
        {'name': 'Gold Roast', 'min_points': 350, 'perk': 'Priority barista brewing + 10% off beans'},
        {'name': 'Platinum Reserve', 'min_points': 700, 'perk': 'Exclusive single-origin tasting events'},
    ]

    current_tier = perk_tiers[0]
    for tier in perk_tiers:
        if total_earned >= tier['min_points']:
            current_tier = tier

    context = {
        'balance': balance,
        'total_earned': total_earned,
        'total_redeemed': total_redeemed,
        'transactions': transactions,
        'rate': rate,
        'perk_tiers': perk_tiers,
        'current_tier': current_tier,
        'title': 'Coffee Rewards & Loyalty Points',
    }
    return render(request, 'loyalty/rewards.html', context)
