from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from orders.models import Order
from orders.cart import Cart
from loyalty.services import award_points_for_order
from .models import Payment
from .services import initiate_khalti_payment, verify_khalti_payment


@login_required
def khalti_initiate_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)

    if order.payment_status == 'PAID':
        messages.info(request, "This order is already paid.")
        return redirect('orders:confirmation', order_number=order.order_number)

    return_url = request.build_absolute_uri(reverse('payments:khalti_verify'))
    website_url = request.build_absolute_uri('/')

    # Attempt to initiate real Khalti API call
    res = initiate_khalti_payment(order, return_url, website_url)

    if res['success']:
        return redirect(res['payment_url'])
    else:
        # If Khalti test credentials are placeholder or network failed, render the Sandbox Test Simulator
        # This guarantees 100% testability while following the exact sandbox flow
        payment, _ = Payment.objects.get_or_create(
            order=order,
            payment_method='KHALTI',
            defaults={'amount': order.total_amount, 'status': 'PENDING'}
        )
        return render(request, 'payments/khalti_sandbox_gateway.html', {
            'order': order,
            'payment': payment,
            'api_notice': res.get('error'),
            'title': 'Khalti Sandbox Payment Simulator'
        })


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

    if not purchase_order_id and pidx:
        # Try finding payment by pidx
        payment_match = Payment.objects.filter(transaction_id=pidx).first()
        if payment_match:
            order = payment_match.order
        else:
            messages.error(request, "Unable to find the order associated with this payment session.")
            return redirect('orders:history')
    elif purchase_order_id:
        order = get_object_or_404(Order, order_number=purchase_order_id, customer=request.user)
    else:
        messages.error(request, "Payment session identifier missing.")
        return redirect('orders:history')

    if order.payment_status == 'PAID':
        messages.info(request, "This order is already paid.")
        return redirect('orders:confirmation', order_number=order.order_number)

    payment = Payment.objects.filter(order=order, payment_method='KHALTI').first()
    if not payment:
        payment = Payment.objects.create(
            order=order,
            payment_method='KHALTI',
            amount=order.total_amount,
            status='PENDING'
        )

    # Backend Verification
    is_verified = False
    if pidx:
        verification_result = verify_khalti_payment(pidx)
        if verification_result.get('success'):
            data = verification_result.get('data', {})
            backend_status = data.get('status')
            payment.raw_response = data
            payment.transaction_id = pidx
            expected_paisa = max(int(Decimal(str(order.total_amount)) * 100), 1000)
            if backend_status == 'Completed':
                if int(data.get('total_amount') or 0) != expected_paisa:
                    payment.status = 'FAILED'
                    payment.save()
                    messages.error(request, "Paid amount does not match the order total. Please contact the shop.")
                    return redirect('orders:detail', order_number=order.order_number)
                is_verified = True
                payment.reference_id = data.get('transaction_id') or txn_id
            elif backend_status in ('Pending', 'Initiated'):
                payment.save()
                messages.info(request, "Your Khalti payment is still being processed. Please check again shortly.")
                return redirect('orders:detail', order_number=order.order_number)
            elif backend_status == 'User canceled':
                payment.status = 'CANCELLED'
                payment.save()
                messages.warning(request, "Payment was cancelled on Khalti.")
                return redirect('orders:detail', order_number=order.order_number)
            else:
                payment.status = 'FAILED'
                payment.save()
                messages.error(request, f"Khalti payment status: {backend_status}")
                return redirect('orders:detail', order_number=order.order_number)
        else:
            # Check if simulation passed via sandbox portal
            if settings.DEBUG and status == 'Completed' and request.GET.get('simulated') == '1':
                is_verified = True
                payment.reference_id = f"KHL-SIM-{timezone.now().strftime('%H%M%S')}"

    if is_verified:
        payment.status = 'PAID'
        payment.save()

        order.payment_status = 'PAID'
        order.order_status = 'CONFIRMED'
        order.save(update_fields=['payment_status', 'order_status'])

        # Award points for paid order
        award_points_for_order(order)

        # Clear cart
        cart = Cart(request)
        cart.clear()

        messages.success(request, f"Payment of Rs. {order.total_amount} via Khalti was successful! Order confirmed.")
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
