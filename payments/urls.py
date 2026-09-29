from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('khalti/initiate/<str:order_number>/', views.khalti_initiate_view, name='khalti_initiate'),
    path('khalti/verify/', views.khalti_verify_view, name='khalti_verify'),
    path('khalti/simulate/<str:order_number>/', views.khalti_simulate_action, name='khalti_simulate'),
]
