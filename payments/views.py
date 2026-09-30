import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from orders.models import Order
from orders.cart import Cart
from products.models import Product
from loyalty.services import award_points_for_order
from .models import Payment
from .services import initiate_khalti_payment, verify_khalti_payment

logger = logging.getLogger(__name__)


@login_required
def khalti_initiate_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)

    if order.payment_status == 'PAID':
        messages.info(request, "This order is already paid.")
        return redirect('orders:confirmation', order_number=order.order_number)

    return_url = request.build_absolute_uri(reverse('payments:khalti_verify'))
    website_url = request.build_absolute_uri('/')

    # Attempt to initiate real Khalti KPG-2 API call
    res = initiate_khalti_payment(order, return_url, website_url)

    if res['success']:
        # Redirect directly to Khalti ePayment gateway
        return redirect(res['payment_url'])
    else:
        logger.error(f"Khalti payment initiation failed for Order #{order.order_number}: {res.get('error')}")
        messages.error(
            request,
            f"Khalti payment initiation failed: {res.get('error')}. Please verify your Khalti secret key in .env or try again."
        )
        return redirect('orders:detail', order_number=order.order_number)


@login_required
def khalti_verify_view(request):
    """
    Callback handler for Khalti return_url.
    Queries Khalti API backend to verify real status.
    """
    pidx = request.GET.get('pidx')
    txn_id = request.GET.get('txnId')
    status = request.GET.get('status')
    purchase_order_id = request.GET.get('purchase_order_id')

    if not pidx:
        messages.error(request, "Missing transaction identifier (pidx) from payment gateway.")
        return redirect('orders:history')

    if not purchase_order_id:
        payment_match = Payment.objects.filter(transaction_id=pidx).select_related('order').first()
        if payment_match:
            order = payment_match.order
        else:
            messages.error(request, "Unable to find the order associated with this payment session.")
            return redirect('orders:history')
    else:
        order = get_object_or_404(Order, order_number=purchase_order_id, customer=request.user)

    # Idempotency: if order is already paid, redirect to confirmation immediately
    if order.payment_status == 'PAID':
        messages.info(request, "This order has already been paid and confirmed.")
        return redirect('orders:confirmation', order_number=order.order_number)

    payment, _ = Payment.objects.get_or_create(
        order=order,
        payment_method='KHALTI',
        defaults={'amount': order.total_amount, 'status': 'PENDING'}
    )

    # Server-side verification with Khalti
    is_verified = False
    simulated = request.GET.get('simulated') == '1'

    if simulated and (settings.DEBUG or getattr(settings, 'TESTING', False)) and status == 'Completed':
        # Simulated verification for testing
        is_verified = True
        payment.transaction_id = pidx
        payment.reference_id = f"KHL-SIM-{timezone.now().strftime('%H%M%S')}"
        payment.raw_response = {
            'pidx': pidx,
            'status': 'Completed',
            'simulated': True,
            'total_amount': int(Decimal(str(order.total_amount)) * 100)
        }
    else:
        verification_result = verify_khalti_payment(pidx)
        if verification_result.get('success'):
            data = verification_result.get('data', {})
            backend_status = data.get('status')
            payment.raw_response = data
            payment.transaction_id = pidx
            expected_paisa = int(Decimal(str(order.total_amount)) * 100)

            if backend_status == 'Completed':
                # Check for amount mismatch
                paid_amount = int(data.get('total_amount') or 0)
                if paid_amount != expected_paisa:
                    logger.warning(
                        f"Khalti amount mismatch for Order #{order.order_number}: "
                        f"Expected {expected_paisa} paisa, received {paid_amount} paisa."
                    )
                    payment.status = 'FAILED'
                    payment.save()
                    messages.error(
                        request,
                        f"Payment amount mismatch. Order requires Rs. {order.total_amount}, but gateway reported Rs. {paid_amount / 100:.2f}. Order remains unpaid."
                    )
                    return redirect('orders:detail', order_number=order.order_number)

                is_verified = True
                payment.reference_id = data.get('transaction_id') or txn_id or pidx
            elif backend_status == 'User canceled':
                payment.status = 'CANCELLED'
                payment.save()
                messages.warning(request, "Payment was cancelled on Khalti. You can try paying again.")
                return redirect('orders:detail', order_number=order.order_number)
            elif backend_status in ('Pending', 'Initiated'):
                payment.status = 'PENDING'
                payment.save()
                messages.info(request, "Your Khalti payment is currently pending confirmation from Khalti.")
                return redirect('orders:detail', order_number=order.order_number)
            elif backend_status == 'Expired':
                payment.status = 'FAILED'
                payment.save()
                messages.error(request, "The payment session expired. Please retry payment.")
                return redirect('orders:detail', order_number=order.order_number)
            else:
                payment.status = 'FAILED'
                payment.save()
                logger.warning(f"Khalti payment failed with status '{backend_status}' for order #{order.order_number}")
                messages.error(request, f"Khalti payment was not completed (Status: {backend_status}).")
                return redirect('orders:detail', order_number=order.order_number)
        else:
            payment.status = 'FAILED'
            payment.save()
            err = verification_result.get('error')
            logger.error(f"Khalti backend verification failed for pidx {pidx}: {err}")
            messages.error(request, f"Payment verification error: {err}. Please try again.")
            return redirect('orders:detail', order_number=order.order_number)

    if is_verified:
        with transaction.atomic():
            # Lock order row for atomic idempotent update
            locked_order = Order.objects.select_for_update().get(id=order.id)
            if locked_order.payment_status != 'PAID':
                # Deduct stock for all items
                for item in locked_order.items.select_related('product'):
                    prod = Product.objects.select_for_update().get(id=item.product.id)
                    prod.stock = max(0, prod.stock - item.quantity)
                    prod.save(update_fields=['stock'])

                # Update payment and order status
                payment.status = 'PAID'
                payment.save()

                locked_order.payment_status = 'PAID'
                locked_order.order_status = 'CONFIRMED'
                locked_order.save(update_fields=['payment_status', 'order_status'])

                # Award loyalty points for paid order
                award_points_for_order(locked_order)

        # Clear cart
        cart = Cart(request)
        cart.clear()

        messages.success(
            request,
            f"Payment of Rs. {order.total_amount} via Khalti was successful! Order #{order.order_number} is confirmed."
        )
        return redirect('orders:confirmation', order_number=order.order_number)
    else:
        messages.error(request, "Payment could not be verified by Khalti servers. Please try again.")
        return redirect('orders:detail', order_number=order.order_number)


@login_required
def khalti_simulate_action(request, order_number):
    """
    Handles Sandbox Mock action (Authorize / Cancel / Fail) for development testing.
    """
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    action = request.POST.get('action')

    if action == 'success':
        return redirect(f"{reverse('payments:khalti_verify')}?purchase_order_id={order.order_number}&pidx=SANDBOX_PIDX_{order.order_number}&status=Completed&simulated=1")
    elif action == 'cancel':
        messages.warning(request, "You cancelled the Khalti Sandbox payment.")
        return redirect('orders:detail', order_number=order.order_number)
    else:
        payment, _ = Payment.objects.get_or_create(
            order=order,
            payment_method='KHALTI',
            defaults={'amount': order.total_amount}
        )
        payment.status = 'FAILED'
        payment.save()
        messages.error(request, "Khalti Sandbox simulation recorded as Failed.")
        return redirect('orders:detail', order_number=order.order_number)
