from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, Product


def product_list_view(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    # Search filter
    search_query = request.GET.get('q', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Category filter from GET query param if category_slug not in path
    cat_param = request.GET.get('category', '').strip()
    if cat_param and not category_slug:
        products = products.filter(category__slug=cat_param)
        try:
            selected_category = Category.objects.get(slug=cat_param)
        except Category.DoesNotExist:
            pass

    # Availability filter
    in_stock_only = request.GET.get('in_stock', '')
    if in_stock_only == '1':
        products = products.filter(stock__gt=0)

    # Sorting
    sort_by = request.GET.get('sort', 'default')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'popular':
        products = products.order_by('-is_popular', '-rating')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:
        products = products.order_by('-is_featured', '-created_at')

    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_count': products.count(),
        'title': f"{selected_category.name} - Menu" if selected_category else "Coffee Menu & Specialties",
    }
    return render(request, 'products/list.html', context)


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
        'title': f"{product.name} | Modern Coffee Shop"
    }
    return render(request, 'products/detail.html', context)
