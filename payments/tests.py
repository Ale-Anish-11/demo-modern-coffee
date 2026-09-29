from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from orders.models import Order
from payments.models import Payment
from loyalty.models import LoyaltyPointTransaction


class PaymentGatewayTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='khalti_user', password='password123')
        self.order = Order.objects.create(
            customer=self.user,
            customer_name='Khalti Tester',
            email='khalti@example.com',
            phone='9840000000',
            total_amount=Decimal('500.00'),
            payment_method='KHALTI',
            payment_status='PENDING'
        )

    def test_payment_initiation_view(self):
        self.client.login(username='khalti_user', password='password123')
        res = self.client.get(reverse('payments:khalti_initiate', args=[self.order.order_number]))
        self.assertEqual(res.status_code, 200) # Renders sandbox simulator gateway when test creds mock

    def test_khalti_verification_flow(self):
        self.client.login(username='khalti_user', password='password123')

        # Simulate verified Khalti return URL
        verify_url = f"{reverse('payments:khalti_verify')}?purchase_order_id={self.order.order_number}&pidx=TEST_PIDX_12345&status=Completed&simulated=1"
        res = self.client.get(verify_url, follow=True)
        self.assertEqual(res.status_code, 200)

        # Refresh order
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.order_status, 'CONFIRMED')

        # Verify Payment record
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, 'PAID')

        # Verify Loyalty points awarded on payment (500 NPR => 50 pts)
        balance = LoyaltyPointTransaction.get_user_balance(self.user)
        self.assertEqual(balance, 50)
