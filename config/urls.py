"""
URL configuration for Modern Coffee Shop project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Core public pages
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    # Django built-in admin
    path('admin/', admin.site.urls),

    # Application endpoints
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('menu/', include('products.urls', namespace='products')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('loyalty/', include('loyalty.urls', namespace='loyalty')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
]

# Static & media file serving during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'config.views.handler404_view'
handler500 = 'config.views.handler500_view'
