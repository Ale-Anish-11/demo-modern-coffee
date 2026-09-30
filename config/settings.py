"""
Django settings for Modern Coffee Shop project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-modern-coffee-shop-super-secret-key-2026-prod')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,*').split(',') if host.strip()]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Local Apps
    'accounts.apps.AccountsConfig',
    'products.apps.ProductsConfig',
    'orders.apps.OrdersConfig',
    'payments.apps.PaymentsConfig',
    'loyalty.apps.LoyaltyConfig',
    'dashboard.apps.DashboardConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'orders.context_processors.cart_context',
                'loyalty.context_processors.loyalty_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# Default is SQLite for zero-setup development, designed for PostgreSQL compatibility
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': BASE_DIR / os.getenv('DATABASE_NAME', 'db.sqlite3'),
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User & product uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# Messages tags mapping for Tailwind alert styles
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'bg-stone-100 text-stone-800 border-stone-300',
    messages.INFO: 'bg-sky-50 text-sky-800 border-sky-300',
    messages.SUCCESS: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    messages.WARNING: 'bg-amber-50 text-amber-800 border-amber-300',
    messages.ERROR: 'bg-rose-50 text-rose-800 border-rose-300',
}

# Cart Session ID
CART_SESSION_ID = 'modern_coffee_cart'

# Khalti Gateway Configuration (KPG-2 ePayment)
KHALTI_BASE_URL = os.getenv('KHALTI_BASE_URL', 'https://dev.khalti.com/api/v2/')
KHALTI_PUBLIC_KEY = os.getenv('KHALTI_PUBLIC_KEY', 'test_public_key_77ca48e7786144e0bcf00e572049e29f')
KHALTI_SECRET_KEY = os.getenv('KHALTI_SECRET_KEY', 'test_secret_key_26b206e987c94488828bbf13e51d141e')
KHALTI_INITIATE_URL = os.getenv('KHALTI_INITIATE_URL', f"{KHALTI_BASE_URL.rstrip('/')}/epayment/initiate/")
KHALTI_LOOKUP_URL = os.getenv('KHALTI_LOOKUP_URL', f"{KHALTI_BASE_URL.rstrip('/')}/epayment/lookup/")

# Loyalty System Configuration
# Every Rs. 100 spent gives 10 points
LOYALTY_POINTS_PER_HUNDRED = int(os.getenv('LOYALTY_POINTS_PER_HUNDRED', 10))
# 1 Point = Rs. 1.00 redemption discount
LOYALTY_POINT_REDEEM_VALUE = float(os.getenv('LOYALTY_POINT_REDEEM_VALUE', 1.0))
