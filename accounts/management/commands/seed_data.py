from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import CustomerProfile
from products.models import Category, Product
from orders.models import Order, OrderItem
from payments.models import Payment
from loyalty.models import LoyaltyPointTransaction


class Command(BaseCommand):
    help = 'Seeds database with initial coffee products, categories, admin user, and sample customer data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seeding...")

        # 1. Superuser / Admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@moderncoffee.com',
                'first_name': 'Admin',
                'last_name': 'Manager',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin12345')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user (admin / admin12345)"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Demo Customer
        customer, c_created = User.objects.get_or_create(
            username='barista_john',
            defaults={
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Barista',
            }
        )
        if c_created:
            customer.set_password('coffee12345')
            customer.save()
            profile, _ = CustomerProfile.objects.get_or_create(user=customer)
            profile.phone = '9841234567'
            profile.address = 'Thamel Marg, Kathmandu'
            profile.save()
            self.stdout.write(self.style.SUCCESS("Created demo customer (barista_john / coffee12345)"))
        else:
            self.stdout.write("Demo customer already exists.")

        # 3. Categories
        categories_data = [
            {'name': 'Espresso', 'slug': 'espresso', 'icon': 'fa-mug-hot', 'description': 'Bold, concentrated shots extracted from freshly ground dark roasts.'},
            {'name': 'Cappuccino', 'slug': 'cappuccino', 'icon': 'fa-cloud', 'description': 'Classic equal parts rich espresso, steamed milk, and velvety milk foam.'},
            {'name': 'Latte', 'slug': 'latte', 'icon': 'fa-heart', 'description': 'Smooth espresso blended with generous silky microfoam and delicate latte art.'},
            {'name': 'Americano', 'slug': 'americano', 'icon': 'fa-tint', 'description': 'Espresso diluted with hot water for a smooth, deep coffee cup.'},
            {'name': 'Mocha', 'slug': 'mocha', 'icon': 'fa-cookie-bite', 'description': 'Decadent fusion of rich espresso, artisan chocolate, and steamed milk.'},
            {'name': 'Cold Coffee', 'slug': 'cold-coffee', 'icon': 'fa-snowflake', 'description': 'Chilled, refreshing brews, iced lattes, and 18-hour cold extractions.'},
            {'name': 'Tea & Matcha', 'slug': 'tea-matcha', 'icon': 'fa-leaf', 'description': 'Premium organic teas, aromatic Himalayan leaves, and ceremonial matcha.'},
            {'name': 'Snacks & Bakery', 'slug': 'snacks-bakery', 'icon': 'fa-bread-slice', 'description': 'Freshly baked croissants, artisanal bagels, and warm savory bites.'},
            {'name': 'Desserts', 'slug': 'desserts', 'icon': 'fa-cake-candles', 'description': 'Handcrafted sweet pastries, tiramisu, and cheesecakes.'},
        ]

        cat_objs = {}
        for c_data in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=c_data['slug'],
                defaults={
                    'name': c_data['name'],
                    'icon': c_data['icon'],
                    'description': c_data['description'],
                }
            )
            cat_objs[c_data['slug']] = cat

        self.stdout.write(self.style.SUCCESS(f"Categories verified: {len(cat_objs)}"))

        # 4. Products
        products_data = [
            {
                'name': 'Himalayan Double Espresso',
                'slug': 'himalayan-double-espresso',
                'category': 'espresso',
                'description': 'A robust double extraction featuring notes of dark cocoa, roasted hazelnuts, and velvety crema sourced from high-altitude Nuwakot Arabica beans.',
                'price': Decimal('160.00'),
                'stock': 45,
                'rating': Decimal('4.9'),
                'reviews_count': 34,
                'is_featured': True,
                'is_popular': True,
                'calories': 5,
                'brew_time': '2 mins',
                'image_url': 'https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Golden Velvet Cappuccino',
                'slug': 'golden-velvet-cappuccino',
                'category': 'cappuccino',
                'description': 'Traditional Italian style cappuccino with rich espresso, perfectly frothed steamed whole milk, and dusted with organic Ceylon cinnamon.',
                'price': Decimal('240.00'),
                'stock': 38,
                'rating': Decimal('4.8'),
                'reviews_count': 56,
                'is_featured': True,
                'is_popular': True,
                'calories': 130,
                'brew_time': '3-4 mins',
                'image_url': 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Vanilla Bean Oat Latte',
                'slug': 'vanilla-bean-oat-latte',
                'category': 'latte',
                'description': 'Silky organic oat milk steamed to perfection with double shot espresso and infused with pure Madagascar vanilla extract.',
                'price': Decimal('290.00'),
                'stock': 50,
                'rating': Decimal('4.9'),
                'reviews_count': 72,
                'is_featured': True,
                'is_popular': True,
                'calories': 160,
                'brew_time': '3-5 mins',
                'image_url': 'https://images.unsplash.com/photo-1541167760496-1628856ab772?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Spanish Honey Cortado',
                'slug': 'spanish-honey-cortado',
                'category': 'latte',
                'description': 'Equal ratio of espresso to warm textured milk cut through with a hint of wild forest honey. Balanced, bold, and slightly sweet.',
                'price': Decimal('210.00'),
                'stock': 30,
                'rating': Decimal('4.7'),
                'reviews_count': 22,
                'is_featured': False,
                'is_popular': True,
                'calories': 95,
                'brew_time': '3 mins',
                'image_url': 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Classic Caffe Americano',
                'slug': 'classic-caffe-americano',
                'category': 'americano',
                'description': 'Double shot of our signature house blend espresso pulled directly over steaming mountain spring water for a crisp, nuanced finish.',
                'price': Decimal('180.00'),
                'stock': 60,
                'rating': Decimal('4.6'),
                'reviews_count': 19,
                'is_featured': False,
                'is_popular': False,
                'calories': 10,
                'brew_time': '2 mins',
                'image_url': 'https://images.unsplash.com/photo-1551030173-122aabc4489c?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Dark Belgian Chocolate Mocha',
                'slug': 'dark-belgian-chocolate-mocha',
                'category': 'mocha',
                'description': 'Melted Belgian 70% dark chocolate combined with espresso, steamed milk, and crowned with freshly whipped cream and chocolate curls.',
                'price': Decimal('320.00'),
                'stock': 25,
                'rating': Decimal('4.9'),
                'reviews_count': 88,
                'is_featured': True,
                'is_popular': True,
                'calories': 310,
                'brew_time': '4-5 mins',
                'image_url': 'https://images.unsplash.com/photo-1578314675249-a6910f80cc4e?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': '18-Hour Nitro Cold Brew',
                'slug': '18-hour-nitro-cold-brew',
                'category': 'cold-coffee',
                'description': 'Single-origin beans steeped in chilled water for 18 hours, infused with nitrogen for a Guinness-like cascade and naturally sweet creaminess.',
                'price': Decimal('280.00'),
                'stock': 20,
                'rating': Decimal('4.9'),
                'reviews_count': 64,
                'is_featured': True,
                'is_popular': True,
                'calories': 5,
                'brew_time': 'Instant tap',
                'image_url': 'https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Iced Caramel Cloud Macchiato',
                'slug': 'iced-caramel-cloud-macchiato',
                'category': 'cold-coffee',
                'description': 'Light and airy cold foam over iced milk, marked with bold espresso shots and drizzled with buttery salted caramel.',
                'price': Decimal('310.00'),
                'stock': 40,
                'rating': Decimal('4.8'),
                'reviews_count': 45,
                'is_featured': False,
                'is_popular': True,
                'calories': 220,
                'brew_time': '3-4 mins',
                'image_url': 'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Ceremonial Uji Matcha Latte',
                'slug': 'ceremonial-uji-matcha-latte',
                'category': 'tea-matcha',
                'description': 'Stone-ground authentic Japanese matcha whisked with bamboo chasen and folded with creamy steamed almond or whole milk.',
                'price': Decimal('340.00'),
                'stock': 28,
                'rating': Decimal('4.8'),
                'reviews_count': 39,
                'is_featured': False,
                'is_popular': True,
                'calories': 140,
                'brew_time': '3 mins',
                'image_url': 'https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Artisanal Butter Croissant',
                'slug': 'artisanal-butter-croissant',
                'category': 'snacks-bakery',
                'description': 'Flaky, golden French croissant laminated with 82% European butter, baked fresh every morning at dawn.',
                'price': Decimal('190.00'),
                'stock': 24,
                'rating': Decimal('4.8'),
                'reviews_count': 51,
                'is_featured': False,
                'is_popular': True,
                'calories': 260,
                'brew_time': 'Warm on request',
                'image_url': 'https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Smoked Turkey & Pesto Panini',
                'slug': 'smoked-turkey-pesto-panini',
                'category': 'snacks-bakery',
                'description': 'Toasted sourdough stuffed with tender smoked turkey, fresh mozzarella, roasted red peppers, and house basil pesto.',
                'price': Decimal('420.00'),
                'stock': 15,
                'rating': Decimal('4.9'),
                'reviews_count': 28,
                'is_featured': False,
                'is_popular': False,
                'calories': 480,
                'brew_time': '6-8 mins',
                'image_url': 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Espresso Tiramisu Jar',
                'slug': 'espresso-tiramisu-jar',
                'category': 'desserts',
                'description': 'Savoiardi ladyfingers soaked in our freshly pulled dark roast espresso and Marsala, layered with sweet mascarpone and Valrhona cocoa.',
                'price': Decimal('360.00'),
                'stock': 18,
                'rating': Decimal('5.0'),
                'reviews_count': 62,
                'is_featured': True,
                'is_popular': True,
                'calories': 380,
                'brew_time': 'Chilled ready',
                'image_url': 'https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'New York Baked Cheesecake',
                'slug': 'new-york-baked-cheesecake',
                'category': 'desserts',
                'description': 'Dense, velvety cream cheese filling with a hint of lemon zest over a crunchy spiced graham cracker butter crust.',
                'price': Decimal('350.00'),
                'stock': 20,
                'rating': Decimal('4.8'),
                'reviews_count': 41,
                'is_featured': False,
                'is_popular': True,
                'calories': 420,
                'brew_time': 'Chilled ready',
                'image_url': 'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=800&q=80',
            },
        ]

        for p_data in products_data:
            cat = cat_objs.get(p_data['category'])
            prod, _ = Product.objects.update_or_create(
                slug=p_data['slug'],
                defaults={
                    'category': cat,
                    'name': p_data['name'],
                    'description': p_data['description'],
                    'price': p_data['price'],
                    'stock': p_data['stock'],
                    'rating': p_data['rating'],
                    'reviews_count': p_data['reviews_count'],
                    'is_featured': p_data['is_featured'],
                    'is_popular': p_data['is_popular'],
                    'calories': p_data['calories'],
                    'brew_time': p_data['brew_time'],
                    'image_url': p_data['image_url'],
                    'available': True,
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Products seeded: {len(products_data)}"))

        # 5. Seed an initial sample order for demo customer so history is rich
        if not Order.objects.filter(customer=customer).exists():
            latte = Product.objects.get(slug='vanilla-bean-oat-latte')
            croissant = Product.objects.get(slug='artisanal-butter-croissant')

            sample_order = Order.objects.create(
                customer=customer,
                customer_name='John Barista',
                email='john@example.com',
                phone='9841234567',
                subtotal=Decimal('480.00'),
                discount_amount=Decimal('0.00'),
                total_amount=Decimal('480.00'),
                payment_method='KHALTI',
                payment_status='PAID',
                order_status='COMPLETED',
                notes='Extra warm oat milk please!'
            )

            OrderItem.objects.create(
                order=sample_order,
                product=latte,
                quantity=1,
                unit_price=latte.price,
                subtotal=latte.price
            )
            OrderItem.objects.create(
                order=sample_order,
                product=croissant,
                quantity=1,
                unit_price=croissant.price,
                subtotal=croissant.price
            )

            Payment.objects.create(
                order=sample_order,
                payment_method='KHALTI',
                transaction_id='SAMPLE-PIDX-998822',
                reference_id='KHL-DEMO-TXN-101',
                amount=sample_order.total_amount,
                status='PAID'
            )

            LoyaltyPointTransaction.objects.create(
                customer=customer,
                order=sample_order,
                points=40,
                transaction_type='EARNED',
                description=f"Earned from Order #{sample_order.order_number}"
            )

            LoyaltyPointTransaction.objects.create(
                customer=customer,
                points=50,
                transaction_type='BONUS',
                description="Welcome bonus for joining Modern Coffee Shop"
            )

            self.stdout.write(self.style.SUCCESS("Sample completed order and loyalty points seeded for demo customer."))

        self.stdout.write(self.style.SUCCESS("All seed data successfully generated!"))
