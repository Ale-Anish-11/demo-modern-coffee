from .cart import Cart


def cart_context(request):
    """
    Context processor to make the shopping cart available across all templates.
    """
    cart = Cart(request)
    return {
        'cart': cart,
        'cart_count': len(cart),
        'cart_subtotal': cart.get_subtotal(),
    }
