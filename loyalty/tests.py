from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from orders.models import Order
from loyalty.models import LoyaltyPointTransaction
from loyalty.services import calculate_points_earned, calculate_discount_for_points, award_points_for_order, redeem_points_for_order


class LoyaltyProgramTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='loyalty_user', password='password123')
        self.order = Order.objects.create(
            customer=self.user,
            customer_name='Loyalty Customer',
            email='loyalty@example.com',
            phone='9811223344',
            total_amount=Decimal('550.00'),
            payment_method='KHALTI',
            payment_status='PAID'
        )

    def test_points_calculation(self):
        # 10 points per Rs. 100 spent -> 550 => 50 points
        points = calculate_points_earned(Decimal('550.00'))
        self.assertEqual(points, 50)

        # Rs. 1000 => 100 points
        self.assertEqual(calculate_points_earned(Decimal('1000.00')), 100)

        # Rs. 80 => 0 points (under 100)
        self.assertEqual(calculate_points_earned(Decimal('80.00')), 0)

    def test_award_points_for_order(self):
        awarded = award_points_for_order(self.order)
        self.assertEqual(awarded, 50)
        
        balance = LoyaltyPointTransaction.get_user_balance(self.user)
        self.assertEqual(balance, 50)

        # Attempt duplicate award should be prevented
        dup = award_points_for_order(self.order)
        self.assertEqual(dup, 0)

    def test_redeem_points_for_order(self):
        # Give initial 100 points
        LoyaltyPointTransaction.objects.create(
            customer=self.user,
            points=100,
            transaction_type='BONUS',
            description='Initial bonus'
        )
        
        discount = redeem_points_for_order(self.order, 60)
        self.assertEqual(discount, Decimal('60.00'))

        remaining_balance = LoyaltyPointTransaction.get_user_balance(self.user)
        self.assertEqual(remaining_balance, 40)
