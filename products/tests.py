from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product


class ProductModelAndViewsTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Espresso', slug='espresso')
        self.product = Product.objects.create(
            category=self.category,
            name='Mountain Espresso',
            slug='mountain-espresso',
            description='Bold mountain espresso',
            price=Decimal('150.00'),
            stock=20,
            available=True
        )

    def test_product_creation(self):
        self.assertEqual(str(self.product), 'Mountain Espresso')
        self.assertTrue(self.product.in_stock)

    def test_product_list_view(self):
        response = self.client.get(reverse('products:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mountain Espresso')

    def test_product_category_filter(self):
        response = self.client.get(reverse('products:category', args=['espresso']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mountain Espresso')

    def test_product_detail_view(self):
        response = self.client.get(reverse('products:detail', args=['mountain-espresso']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mountain Espresso')
        self.assertContains(response, '150.00')

    def test_out_of_stock_property(self):
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.in_stock)
