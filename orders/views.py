from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied
from products.models import Product
from loyalty.models import LoyaltyPointTransaction
from loyalty.services import redeem_points_for_order, calculate_points_earned
from payments.models import Payment
from .cart import Cart
from .models import Order, OrderItem


def cart_detail_view(request):
    cart = Cart(request)
    subtotal = cart.get_subtotal()

    # Calculate potential loyalty points earned for this cart
    potential_points = calculate_points_earned(subtotal)

    context = {
        'cart': cart,
        'subtotal': subtotal,
        'potential_points': potential_points,
        'title': 'Your Coffee Cart'
    }
    return render(request, 'orders/cart.html', context)


def cart_add_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    cart = Cart(request)

    if product.stock <= 0:
        messages.error(request, f"Sorry, {product.name} is currently out of stock.")
        return redirect(request.META.get('HTTP_REFERER', 'products:list'))

    try:
        qty = int(request.POST.get('quantity', 1))
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    added_qty = cart.add(product=product, quantity=qty)
    messages.success(request, f"Added {added_qty}x {product.name} to your coffee cart.")

    if request.POST.get('buy_now') == '1':
        return redirect('orders:checkout')

    return redirect(request.META.get('HTTP_REFERER', 'orders:cart_detail'))


def cart_update_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    action = request.POST.get('action')

    if action == 'increment':
        cart.update_quantity(product, 1)
    elif action == 'decrement':
        cart.update_quantity(product, -1)
    elif action == 'set':
        try:
            qty = int(request.POST.get('quantity', 1))
            cart.add(product, quantity=qty, override_quantity=True)
        except (ValueError, TypeError):
            pass

    return redirect('orders:cart_detail')


def cart_remove_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.info(request, f"Removed {product.name} from your cart.")
    return redirect('orders:cart_detail')


@login_required
def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is currently empty. Please add items before checking out.")
        return redirect('products:list')

    user = request.user
    profile = getattr(user, 'profile', None)
    user_points = LoyaltyPointTransaction.get_user_balance(user)
    subtotal = cart.get_subtotal()

    # Pre-validate stock for all items
    out_of_stock_items = []
    for item in cart:
        product = item['product']
        if product.stock < item['quantity']:
            out_of_stock_items.append(f"{product.name} (Only {product.stock} left)")

    if out_of_stock_items:
        messages.error(request, f"Stock insufficient for: {', '.join(out_of_stock_items)}. Please adjust quantities.")
        return redirect('orders:cart_detail')

    if request.method == 'POST':
        customer_name = request.POST.get('full_name', '').strip() or user.get_full_name() or user.username
        email = request.POST.get('email', '').strip() or user.email
        phone = request.POST.get('phone', '').strip() or (profile and profile.phone) or ''
        notes = request.POST.get('notes', '').strip()
        payment_method = request.POST.get('payment_method', 'COUNTER')
        redeem_points_requested = 0

        if request.POST.get('apply_points') == '1':
            try:
                redeem_points_requested = int(request.POST.get('points_to_redeem', 0))
                if redeem_points_requested < 0:
                    redeem_points_requested = 0
            except (ValueError, TypeError):
                redeem_points_requested = 0

        # Points validation
        if redeem_points_requested > user_points:
            redeem_points_requested = user_points

        # Calculate discount safely on server
        discount = Decimal('0.00')
        if redeem_points_requested > 0:
            discount = Decimal(str(redeem_points_requested)) * Decimal('1.0')
            if discount > subtotal:
                discount = subtotal
                redeem_points_requested = int(subtotal)

        final_total = subtotal - discount
        if final_total < Decimal('0.00'):
            final_total = Decimal('0.00')

        if not phone:
            messages.error(request, "Please provide a valid contact phone number.")
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'subtotal': subtotal,
                'user_points': user_points,
                'customer_name': customer_name,
                'email': email,
                'phone': phone,
                'notes': notes,
                'title': 'Secure Checkout'
            })

        try:
            with transaction.atomic():
                # Re-verify and lock items stock
                for item in cart:
                    prod = Product.objects.select_for_update().get(id=item['product'].id)
                    if prod.stock < item['quantity']:
                        raise ValueError(f"Sorry, {prod.name} ran out of stock just now.")
                    # Deduct stock immediately for Pay at Counter; for Khalti, stock is deducted upon verified payment
                    if payment_method == 'COUNTER':
                        prod.stock -= item['quantity']
                        prod.save(update_fields=['stock'])

                # Create Order
                order = Order.objects.create(
                    customer=user,
                    customer_name=customer_name,
                    email=email,
                    phone=phone,
                    notes=notes,
                    subtotal=subtotal,
                    discount_amount=discount,
                    points_redeemed=redeem_points_requested,
                    total_amount=final_total,
                    payment_method=payment_method,
                    payment_status='PENDING',
                    order_status='CONFIRMED' if payment_method == 'COUNTER' else 'PENDING'
                )

                # Create Order Items
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        quantity=item['quantity'],
                        unit_price=item['price'],
                        subtotal=item['total_price']
                    )

                # Process Points Deduction if points were redeemed
                if redeem_points_requested > 0:
                    redeem_points_for_order(order, redeem_points_requested)

                # Handle Payment Routing
                if payment_method == 'KHALTI':
                    # Order is pending until Khalti payment is verified
                    return redirect('payments:khalti_initiate', order_number=order.order_number)
                else:
                    # Pay at Counter
                    Payment.objects.create(
                        order=order,
                        payment_method='COUNTER',
                        amount=final_total,
                        status='PENDING'
                    )
                    cart.clear()
                    messages.success(
                        request,
                        f"Order placed successfully! Order #{order.order_number}. Please pay Rs. {final_total} at the counter upon pickup."
                    )
                    return redirect('orders:confirmation', order_number=order.order_number)

        except Exception as e:
            messages.error(request, f"Order placement failed: {str(e)}")
            return redirect('orders:checkout')

    # GET request
    initial_name = user.get_full_name() or user.username
    initial_email = user.email
    initial_phone = profile.phone if profile else ''
    initial_notes = ''

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'subtotal': subtotal,
        'user_points': user_points,
        'customer_name': initial_name,
        'email': initial_email,
        'phone': initial_phone,
        'notes': initial_notes,
        'title': 'Secure Checkout'
    })


@login_required
def order_confirmation_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    # Object-level ownership protection
    if order.customer != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this order.")

    return render(request, 'orders/confirmation.html', {
        'order': order,
        'title': f"Order Confirmation #{order.order_number}"
    })


@login_required
def order_receipt_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    # Object-level authorization
    if order.customer != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have access to this receipt.")

    payment = order.payments.first()

    return render(request, 'orders/receipt.html', {
        'order': order,
        'payment': payment,
        'title': f"Receipt - Order #{order.order_number}"
    })


@login_required
def order_history_view(request):
    # Customer only sees their own orders
    orders = Order.objects.filter(customer=request.user).prefetch_related('items__product')
    return render(request, 'orders/history.html', {
        'orders': orders,
        'title': 'My Order History'
    })


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    # Authorization
    if order.customer != request.user and not request.user.is_staff:
        raise PermissionDenied("You are not authorized to view this order.")

    payments = order.payments.all()
    return render(request, 'orders/detail.html', {
        'order': order,
        'payments': payments,
        'title': f"Order Details #{order.order_number}"
    })
