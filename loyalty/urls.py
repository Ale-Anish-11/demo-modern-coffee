from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    path('', views.rewards_dashboard_view, name='rewards'),
]
