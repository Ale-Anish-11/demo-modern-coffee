from django.shortcuts import render
from django.contrib import messages
from products.models import Product, Category
from django.conf import settings


def home_view(request):
    featured_products = Product.objects.filter(is_featured=True, available=True)[:4]
    popular_products = Product.objects.filter(is_popular=True, available=True)[:6]
    categories = Category.objects.all()[:6]
    points_rate = getattr(settings, 'LOYALTY_POINTS_PER_HUNDRED', 10)

    context = {
        'featured_products': featured_products,
        'popular_products': popular_products,
        'categories': categories,
        'points_rate': points_rate,
        'title': 'Modern Coffee Shop | Premium Handcrafted Coffee',
    }
    return render(request, 'home.html', context)


def about_view(request):
    return render(request, 'about.html', {'title': 'Our Story | Modern Coffee Shop'})


def contact_view(request):
    if request.method == 'POST':
        messages.success(request, "Thank you for reaching out! Our team will respond to your message shortly.")
    return render(request, 'contact.html', {'title': 'Contact & Location | Modern Coffee Shop'})


def handler404_view(request, exception=None):
    return render(request, '404.html', {'title': 'Page Not Found'}, status=404)


def handler500_view(request):
    return render(request, '500.html', {'title': 'Server Error'}, status=500)
