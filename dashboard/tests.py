from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from orders.models import Order


class DashboardAccessTest(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff_member',
            password='StaffPassword123',
            is_staff=True
        )
        self.customer = User.objects.create_user(
            username='normal_customer',
            password='CustomerPassword123',
            is_staff=False
        )
        self.category = Category.objects.create(name='Tea', slug='tea')
        self.product = Product.objects.create(
            category=self.category,
            name='Green Tea',
            slug='green-tea',
            description='Refreshing tea',
            price=Decimal('120.00'),
            stock=15
        )

    def test_customer_dashboard_access(self):
        self.client.login(username='normal_customer', password='CustomerPassword123')
        res = self.client.get(reverse('dashboard:customer_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'normal_customer')

    def test_staff_portal_denies_normal_customer(self):
        self.client.login(username='normal_customer', password='CustomerPassword123')
        res = self.client.get(reverse('dashboard:admin_overview'))
        # Should redirect to login because not staff
        self.assertEqual(res.status_code, 302)

    def test_staff_portal_allows_staff_user(self):
        self.client.login(username='staff_member', password='StaffPassword123')
        res = self.client.get(reverse('dashboard:admin_overview'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Staff & Owner Management Portal')

    def test_staff_orders_and_products_list(self):
        self.client.login(username='staff_member', password='StaffPassword123')
        
        # Test orders list
        orders_res = self.client.get(reverse('dashboard:admin_orders'))
        self.assertEqual(orders_res.status_code, 200)

        # Test products list
        prods_res = self.client.get(reverse('dashboard:admin_products'))
        self.assertEqual(prods_res.status_code, 200)
        self.assertContains(prods_res, 'Green Tea')
