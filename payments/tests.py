from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from orders.models import Order, OrderItem
from payments.models import Payment
from loyalty.models import LoyaltyPointTransaction


class PaymentGatewayTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='khalti_user', password='password123')
        self.category = Category.objects.create(name='Coffee', slug='coffee')
        self.product = Product.objects.create(
            category=self.category,
            name='Espresso',
            slug='espresso',
            price=Decimal('250.00'),
            stock=10,
            available=True
        )
        self.order = Order.objects.create(
            customer=self.user,
            customer_name='Khalti Tester',
            email='khalti@example.com',
            phone='9840000000',
            subtotal=Decimal('500.00'),
            total_amount=Decimal('500.00'),
            payment_method='KHALTI',
            payment_status='PENDING',
            order_status='PENDING'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('250.00'),
            subtotal=Decimal('500.00')
        )
        self.client.login(username='khalti_user', password='password123')

    @patch('payments.views.initiate_khalti_payment')
    def test_payment_initiation_success(self, mock_initiate):
        """Tests successful payment initiation redirects to Khalti payment_url."""
        mock_initiate.return_value = {
            'success': True,
            'payment_url': 'https://test-pay.khalti.com/?pidx=TEST_PIDX_001',
            'pidx': 'TEST_PIDX_001'
        }
        res = self.client.get(reverse('payments:khalti_initiate', args=[self.order.order_number]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, 'https://test-pay.khalti.com/?pidx=TEST_PIDX_001')

    @patch('payments.views.verify_khalti_payment')
    def test_1_normal_successful_payment(self, mock_verify):
        """
        Test 1: Normal successful Khalti payment.
        Expected: Order -> Paid, Payment -> Successful, Stock -> Correctly updated, Confirmation -> Displayed.
        """
        mock_verify.return_value = {
            'success': True,
            'data': {
                'status': 'Completed',
                'total_amount': 50000, # 500 NPR in paisa
                'transaction_id': 'TXN_KHALTI_999'
            }
        }
        verify_url = f"{reverse('payments:khalti_verify')}?purchase_order_id={self.order.order_number}&pidx=PIDX_SUCCESS&status=Completed"
        res = self.client.get(verify_url, follow=True)
        self.assertEqual(res.status_code, 200)

        # 1. Order marked paid & confirmed
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.order_status, 'CONFIRMED')

        # 2. Payment marked successful
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, 'PAID')
        self.assertEqual(payment.reference_id, 'TXN_KHALTI_999')

        # 3. Stock correctly updated (10 - 2 = 8)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        # 4. Confirmation page displayed
        self.assertContains(res, self.order.order_number)

    @patch('payments.views.verify_khalti_payment')
    def test_2_failed_payment(self, mock_verify):
        """
        Test 2: Failed payment.
        Expected: Order is NOT marked paid. Stock NOT deducted.
        """
        mock_verify.return_value = {
            'success': True,
            'data': {'status': 'Failed', 'total_amount': 50000}
        }
        verify_url = f"{reverse('payments:khalti_verify')}?purchase_order_id={self.order.order_number}&pidx=PIDX_FAIL&status=Failed"
        res = self.client.get(verify_url, follow=True)
        self.assertEqual(res.status_code, 200)

        self.order.refresh_from_db()
        self.assertNotEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.payment_status, 'PENDING')

        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, 'FAILED')

        # Stock must NOT be deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    @patch('payments.views.verify_khalti_payment')
    def test_3_cancelled_payment(self, mock_verify):
        """
        Test 3: Cancelled payment.
        Expected: Order remains unpaid/pending. Stock NOT deducted.
        """
        mock_verify.return_value = {
            'success': True,
            'data': {'status': 'User canceled', 'total_amount': 50000}
        }
        verify_url = f"{reverse('payments:khalti_verify')}?purchase_order_id={self.order.order_number}&pidx=PIDX_CANCEL&status=User%20canceled"
        res = self.client.get(verify_url, follow=True)
        self.assertEqual(res.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PENDING')

        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, 'CANCELLED')

        # Stock must NOT be deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    @patch('payments.views.verify_khalti_payment')
    def test_4_amount_mismatch(self, mock_verify):
        """
        Test 4: Amount mismatch.
        Expected: Payment rejected and order remains unpaid. Stock NOT deducted.
        """
        # Order requires 500 NPR (50000 paisa), but gateway reported 300 NPR (30000 paisa)
        mock_verify.return_value = {
            'success': True,
            'data': {'status': 'Completed', 'total_amount': 30000}
        }
        verify_url = f"{reverse('payments:khalti_verify')}?purchase_order_id={self.order.order_number}&pidx=PIDX_TAMPER&status=Completed"
        res = self.client.get(verify_url, follow=True)
        self.assertEqual(res.status_code, 200)

        self.order.refresh_from_db()
        self.assertNotEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.payment_status, 'PENDING')

        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, 'FAILED')

        # Stock must NOT be deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    @patch('payments.views.verify_khalti_payment')
    def test_5_duplicate_callback(self, mock_verify):
        """
        Test 5: Duplicate callback.
        Expected: No duplicate payment or stock deduction.
        """
        mock_verify.return_value = {
            'success': True,
            'data': {
                'status': 'Completed',
                'total_amount': 50000,
                'transaction_id': 'TXN_DUP_01'
            }
        }
        verify_url = f"{reverse('payments:khalti_verify')}?purchase_order_id={self.order.order_number}&pidx=PIDX_DUP&status=Completed"

        # First callback
        self.client.get(verify_url, follow=True)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        # Second identical callback
        res2 = self.client.get(verify_url, follow=True)
        self.assertEqual(res2.status_code, 200)

        # Stock must NOT be deducted a second time
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        # Only one payment record exists
        self.assertEqual(Payment.objects.filter(order=self.order).count(), 1)

    def test_6_already_paid_order_callback(self):
        """
        Test 6: Already-paid order callback.
        Expected: No second payment processing.
        """
        self.order.payment_status = 'PAID'
        self.order.order_status = 'CONFIRMED'
        self.order.save()

        verify_url = f"{reverse('payments:khalti_verify')}?purchase_order_id={self.order.order_number}&pidx=PIDX_ANY&status=Completed"
        res = self.client.get(verify_url, follow=True)
        self.assertEqual(res.status_code, 200)

        # Stock remains unchanged
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_7_invalid_pidx(self):
        """
        Test 7: Invalid pidx / missing pidx.
        Expected: Safe failure without crashing the application.
        """
        # Missing pidx
        res1 = self.client.get(reverse('payments:khalti_verify'), follow=True)
        self.assertEqual(res1.status_code, 200)

        # Non-existent order
        res2 = self.client.get(f"{reverse('payments:khalti_verify')}?pidx=INVALID_PIDX&purchase_order_id=NON_EXISTENT", follow=True)
        self.assertEqual(res2.status_code, 404)

    @patch('payments.views.verify_khalti_payment')
    def test_8_api_network_failure(self, mock_verify):
        """
        Test 8: Khalti API/network failure.
        Expected: Graceful error and recoverable checkout state.
        """
        mock_verify.return_value = {
            'success': False,
            'error': 'Gateway timeout / connection issue'
        }
        verify_url = f"{reverse('payments:khalti_verify')}?purchase_order_id={self.order.order_number}&pidx=PIDX_NET_ERR"
        res = self.client.get(verify_url, follow=True)
        self.assertEqual(res.status_code, 200)

        # Order remains pending and recoverable
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PENDING')

        # Stock is intact
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
