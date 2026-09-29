from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from orders.models import Order
from orders.cart import Cart


class OrderAndCartTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='customer1', email='cust1@example.com', password='Password123')
        self.other_user = User.objects.create_user(username='customer2', email='cust2@example.com', password='Password123')
        
        self.category = Category.objects.create(name='Brew', slug='brew')
        self.product = Product.objects.create(
            category=self.category,
            name='Americano',
            slug='americano',
            description='Crisp brew',
            price=Decimal('200.00'),
            stock=10,
            available=True
        )

    def test_cart_operations(self):
        self.client.login(username='customer1', password='Password123')
        
        # Add to cart
        add_url = reverse('orders:cart_add', args=[self.product.id])
        response = self.client.post(add_url, {'quantity': 2}, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check cart page
        cart_url = reverse('orders:cart_detail')
        cart_res = self.client.get(cart_url)
        self.assertContains(cart_res, 'Americano')
        self.assertContains(cart_res, '400.00')

    def test_pay_at_counter_checkout(self):
        self.client.login(username='customer1', password='Password123')
        
        # Add product to cart
        self.client.post(reverse('orders:cart_add', args=[self.product.id]), {'quantity': 2})

        # Checkout
        checkout_url = reverse('orders:checkout')
        payload = {
            'full_name': 'Customer One',
            'email': 'cust1@example.com',
            'phone': '9800000000',
            'payment_method': 'COUNTER',
            'notes': 'Extra hot',
        }
        res = self.client.post(checkout_url, payload, follow=True)
        self.assertEqual(res.status_code, 200)

        # Verify Order created
        order = Order.objects.get(customer=self.user)
        self.assertEqual(order.payment_method, 'COUNTER')
        self.assertEqual(order.payment_status, 'PENDING')
        self.assertEqual(order.total_amount, Decimal('400.00'))

        # Stock deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_order_object_level_permission(self):
        # Create order for user 1
        order = Order.objects.create(
            customer=self.user,
            customer_name='Customer One',
            email='cust1@example.com',
            phone='9800000000',
            total_amount=Decimal('200.00'),
            payment_method='COUNTER'
        )

        # Log in as user 2 and attempt to view user 1's order
        self.client.login(username='customer2', password='Password123')
        res = self.client.get(reverse('orders:detail', args=[order.order_number]))
        self.assertEqual(res.status_code, 403) # PermissionDenied!
