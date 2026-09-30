import logging
import requests
from decimal import Decimal
from django.conf import settings
from .models import Payment

logger = logging.getLogger(__name__)


def initiate_khalti_payment(order, return_url, website_url):
    """
    Calls Khalti ePayment API v2 to initiate payment session.
    Keeps secret key safely on backend.
    """
    amount_in_paisa = int(Decimal(str(order.total_amount)) * 100)

    # Minimum amount in Khalti is 10 NPR (1000 paisa)
    if amount_in_paisa < 1000:
        amount_in_paisa = 1000

    payload = {
        "return_url": return_url,
        "website_url": website_url,
        "amount": amount_in_paisa,
        "purchase_order_id": order.order_number,
        "purchase_order_name": f"Modern Coffee Shop - Order #{order.order_number}",
        "customer_info": {
            "name": order.customer_name or order.customer.get_full_name() or order.customer.username,
            "email": order.email or order.customer.email or "customer@example.com",
            "phone": order.phone or "9800000000"
        }
    }

    # Optional item breakdown for Khalti checkout UI
    items = list(order.items.select_related('product').all())
    if items:
        payload["product_details"] = [
            {
                "identity": str(item.product.id),
                "name": item.product.name,
                "total_price": int(Decimal(str(item.subtotal)) * 100),
                "quantity": item.quantity,
                "unit_price": int(Decimal(str(item.unit_price)) * 100)
            }
            for item in items
        ]

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            settings.KHALTI_INITIATE_URL,
            json=payload,
            headers=headers,
            timeout=15
        )
        data = response.json()
        if response.status_code == 200 and 'payment_url' in data:
            # Store or update initial pending payment record (idempotent for retries)
            Payment.objects.update_or_create(
                order=order,
                payment_method='KHALTI',
                defaults={
                    'transaction_id': data.get('pidx'),
                    'amount': order.total_amount,
                    'status': 'PENDING',
                    'raw_response': data
                }
            )
            return {
                'success': True,
                'payment_url': data['payment_url'],
                'pidx': data['pidx']
            }
        else:
            logger.warning(f"Khalti initiate API response: {response.status_code} - {data}")
            return {
                'success': False,
                'error': data.get('detail') or data.get('message') or "Khalti API rejected initialization request."
            }
    except Exception as e:
        logger.error(f"Khalti connection error: {str(e)}")
        return {
            'success': False,
            'error': f"Payment gateway connection issue: {str(e)}"
        }


def verify_khalti_payment(pidx):
    """
    Calls Khalti ePayment API v2 lookup to verify payment status on backend.
    """
    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"pidx": pidx}

    try:
        response = requests.post(
            settings.KHALTI_LOOKUP_URL,
            json=payload,
            headers=headers,
            timeout=15
        )
        data = response.json()
        if response.status_code == 200:
            return {'success': True, 'data': data}
        else:
            logger.warning(f"Khalti lookup API response: {response.status_code} - {data}")
            return {'success': False, 'error': data.get('detail') or 'Verification failed with status code'}
    except Exception as e:
        logger.error(f"Khalti lookup connection error: {str(e)}")
        return {'success': False, 'error': str(e)}
