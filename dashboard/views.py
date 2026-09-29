from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from products.models import Product, Category
from orders.models import Order, OrderItem
from payments.models import Payment
from loyalty.models import LoyaltyPointTransaction
from loyalty.services import award_points_for_order
from .forms import ProductForm, CategoryForm


@login_required
def customer_dashboard_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    # Loyalty metrics
    current_points = LoyaltyPointTransaction.get_user_balance(user)
    total_earned = LoyaltyPointTransaction.get_total_earned(user)
    total_redeemed = LoyaltyPointTransaction.get_total_redeemed(user)

    # Recent orders
    recent_orders = Order.objects.filter(customer=user).order_by('-created_at')[:5]
    total_orders_count = Order.objects.filter(customer=user).count()

    # Recent loyalty activity
    recent_points_history = LoyaltyPointTransaction.objects.filter(customer=user).order_by('-created_at')[:5]

    context = {
        'user': user,
        'profile': profile,
        'current_points': current_points,
        'total_earned': total_earned,
        'total_redeemed': total_redeemed,
        'recent_orders': recent_orders,
        'total_orders_count': total_orders_count,
        'recent_points_history': recent_points_history,
        'title': 'Customer Dashboard',
    }
    return render(request, 'dashboard/customer_dashboard.html', context)


# Staff / Admin Custom Dashboard Views
@staff_member_required(login_url='accounts:login')
def admin_overview_view(request):
    today = timezone.now().date()

    # Core Stats
    total_customers = User.objects.filter(is_staff=False).count()
    total_orders = Order.objects.count()
    todays_orders = Order.objects.filter(created_at__date=today).count()

    sales_aggregate = Order.objects.filter(payment_status='PAID').aggregate(total=Sum('total_amount'))
    total_sales = sales_aggregate['total'] or Decimal('0.00')

    pending_orders = Order.objects.filter(order_status='PENDING').count()
    completed_orders = Order.objects.filter(order_status='COMPLETED').count()
    total_products = Product.objects.count()

    # Points issued
    points_issued = LoyaltyPointTransaction.objects.filter(points__gt=0).aggregate(total=Sum('points'))['total'] or 0

    # Popular coffee items
    popular_products = Product.objects.filter(available=True).order_by('-is_popular', '-stock')[:5]

    # Recent 6 orders
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:6]

    # Recent 5 payments
    recent_payments = Payment.objects.select_related('order').order_by('-created_at')[:5]

    context = {
        'total_customers': total_customers,
        'total_orders': total_orders,
        'todays_orders': todays_orders,
        'total_sales': total_sales,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_products': total_products,
        'points_issued': points_issued,
        'popular_products': popular_products,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'title': 'Owner & Staff Admin Portal',
    }
    return render(request, 'dashboard/admin/overview.html', context)


@staff_member_required(login_url='accounts:login')
def admin_orders_list_view(request):
    orders = Order.objects.select_related('customer').prefetch_related('items').order_by('-created_at')

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(customer_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    # Order status filter
    status_filter = request.GET.get('order_status')
    if status_filter:
        orders = orders.filter(order_status=status_filter)

    # Payment status filter
    payment_filter = request.GET.get('payment_status')
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'q': q,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'payment_choices': Order.PAYMENT_STATUS_CHOICES,
        'title': 'Manage Customer Orders',
    }
    return render(request, 'dashboard/admin/orders_list.html', context)


@staff_member_required(login_url='accounts:login')
def admin_order_update_status_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        new_order_status = request.POST.get('order_status')
        new_payment_status = request.POST.get('payment_status')

        if new_order_status in dict(Order.ORDER_STATUS_CHOICES):
            order.order_status = new_order_status

        if new_payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
            old_payment_status = order.payment_status
            order.payment_status = new_payment_status

            # If marked as PAID now, award loyalty points
            if new_payment_status == 'PAID' and old_payment_status != 'PAID':
                award_points_for_order(order)
                # Also update corresponding Payment record
                payment = order.payments.first()
                if payment:
                    payment.status = 'PAID'
                    payment.save(update_fields=['status'])

        order.save()
        messages.success(request, f"Updated Order #{order.order_number} to {order.get_order_status_display()} ({order.get_payment_status_display()}).")

    return redirect(request.META.get('HTTP_REFERER') or 'dashboard:admin_orders')


@staff_member_required(login_url='accounts:login')
def admin_products_list_view(request):
    products = Product.objects.select_related('category').order_by('category__name', 'name')
    categories = Category.objects.all()

    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(name__icontains=q)

    context = {
        'products': products,
        'categories': categories,
        'selected_category_id': category_id,
        'q': q,
        'title': 'Product Inventory Management',
    }
    return render(request, 'dashboard/admin/products_list.html', context)


@staff_member_required(login_url='accounts:login')
def admin_product_create_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' created successfully.")
            return redirect('dashboard:admin_products')
    else:
        form = ProductForm()

    return render(request, 'dashboard/admin/product_form.html', {
        'form': form,
        'title': 'Add New Coffee Product'
    })


@staff_member_required(login_url='accounts:login')
def admin_product_edit_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('dashboard:admin_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'dashboard/admin/product_form.html', {
        'form': form,
        'product': product,
        'title': f"Edit {product.name}"
    })


@staff_member_required(login_url='accounts:login')
def admin_product_delete_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' has been deleted.")
        return redirect('dashboard:admin_products')

    return render(request, 'dashboard/admin/product_confirm_delete.html', {
        'product': product,
        'title': f"Delete {product.name}?"
    })


@staff_member_required(login_url='accounts:login')
def admin_customers_list_view(request):
    customers = User.objects.filter(is_staff=False).select_related('profile').annotate(
        order_count=Count('orders', distinct=True)
    ).order_by('-date_joined')

    q = request.GET.get('q', '').strip()
    if q:
        customers = customers.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )

    # Attach points balance safely
    customers_data = []
    for customer in customers:
        points = LoyaltyPointTransaction.get_user_balance(customer)
        customers_data.append({
            'user': customer,
            'points': points,
        })

    context = {
        'customers_data': customers_data,
        'q': q,
        'title': 'Registered Customers',
    }
    return render(request, 'dashboard/admin/customers_list.html', context)


@staff_member_required(login_url='accounts:login')
def admin_customer_detail_view(request, user_id):
    customer = get_object_or_404(User, id=user_id, is_staff=False)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    points_balance = LoyaltyPointTransaction.get_user_balance(customer)
    points_history = LoyaltyPointTransaction.objects.filter(customer=customer).order_by('-created_at')

    context = {
        'customer': customer,
        'orders': orders,
        'points_balance': points_balance,
        'points_history': points_history,
        'title': f"Customer: {customer.get_full_name() or customer.username}",
    }
    return render(request, 'dashboard/admin/customer_detail.html', context)


@staff_member_required(login_url='accounts:login')
def admin_payments_list_view(request):
    payments = Payment.objects.select_related('order', 'order__customer').order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)

    method_filter = request.GET.get('method')
    if method_filter:
        payments = payments.filter(payment_method=method_filter)

    context = {
        'payments': payments,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'title': 'Payment Transactions Log',
    }
    return render(request, 'dashboard/admin/payments_list.html', context)
