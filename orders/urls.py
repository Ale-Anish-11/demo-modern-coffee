from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add_view, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update_view, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove_view, name='cart_remove'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirmation/<str:order_number>/', views.order_confirmation_view, name='confirmation'),
    path('receipt/<str:order_number>/', views.order_receipt_view, name='receipt'),
    path('history/', views.order_history_view, name='history'),
    path('detail/<str:order_number>/', views.order_detail_view, name='detail'),
]
