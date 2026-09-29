from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Customer Dashboard
    path('', views.customer_dashboard_view, name='customer_dashboard'),

    # Admin / Staff Portal
    path('staff/', views.admin_overview_view, name='admin_overview'),
    path('staff/orders/', views.admin_orders_list_view, name='admin_orders'),
    path('staff/orders/<str:order_number>/status/', views.admin_order_update_status_view, name='admin_order_update_status'),
    path('staff/products/', views.admin_products_list_view, name='admin_products'),
    path('staff/products/add/', views.admin_product_create_view, name='admin_product_create'),
    path('staff/products/<int:pk>/edit/', views.admin_product_edit_view, name='admin_product_edit'),
    path('staff/products/<int:pk>/delete/', views.admin_product_delete_view, name='admin_product_delete'),
    path('staff/customers/', views.admin_customers_list_view, name='admin_customers'),
    path('staff/customers/<int:user_id>/', views.admin_customer_detail_view, name='admin_customer_detail'),
    path('staff/payments/', views.admin_payments_list_view, name='admin_payments'),
]
