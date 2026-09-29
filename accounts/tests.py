from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import CustomerProfile
from loyalty.models import LoyaltyPointTransaction


class AccountsTest(TestCase):
    def test_customer_registration_and_welcome_points(self):
        register_url = reverse('accounts:register')
        payload = {
            'full_name': 'Ram Sharma',
            'username': 'ramsharma',
            'email': 'ram@example.com',
            'phone': '9841112233',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        }
        response = self.client.post(register_url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify user created
        user = User.objects.get(username='ramsharma')
        self.assertEqual(user.email, 'ram@example.com')
        self.assertEqual(user.first_name, 'Ram')
        self.assertEqual(user.last_name, 'Sharma')

        # Verify profile phone
        profile = CustomerProfile.objects.get(user=user)
        self.assertEqual(profile.phone, '9841112233')

        # Verify welcome bonus loyalty points
        balance = LoyaltyPointTransaction.get_user_balance(user)
        self.assertEqual(balance, 50)

    def test_login_and_logout(self):
        user = User.objects.create_user(username='testcoffee', email='test@coffee.com', password='CoffeePassword123')
        
        # Login
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testcoffee',
            'password': 'CoffeePassword123',
            'remember_me': False,
        }, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)

        # Logout
        logout_response = self.client.get(reverse('accounts:logout'), follow=True)
        self.assertFalse(logout_response.context['user'].is_authenticated)
