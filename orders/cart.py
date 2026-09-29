from decimal import Decimal
from django.conf import settings
from products.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity with strict stock bounds.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }

        # Check stock limits
        current_qty = self.cart[product_id]['quantity']
        if override_quantity:
            new_qty = quantity
        else:
            new_qty = current_qty + quantity

        # Clamp to stock
        if new_qty > product.stock:
            new_qty = product.stock

        if new_qty <= 0:
            self.remove(product)
            return 0
        else:
            self.cart[product_id]['quantity'] = new_qty
            # Always ensure server-side price freshness
            self.cart[product_id]['price'] = str(product.price)
            self.save()
            return new_qty

    def remove(self, product):
        """
        Remove a product completely from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update_quantity(self, product, delta):
        """
        Increment or decrement quantity by delta (e.g. +1 or -1).
        """
        product_id = str(product.id)
        if product_id in self.cart:
            new_qty = self.cart[product_id]['quantity'] + delta
            if new_qty <= 0:
                self.remove(product)
                return 0
            if new_qty > product.stock:
                new_qty = product.stock
            self.cart[product_id]['quantity'] = new_qty
            self.save()
            return new_qty
        return 0

    def save(self):
        self.session.modified = True

    def clear(self):
        """
        Remove all items from session cart.
        """
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and query latest product details from DB.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            if 'product' in item:
                # Use current server-side product price
                product = item['product']
                item['price'] = Decimal(str(product.price))
                item['total_price'] = item['price'] * item['quantity']
                item['is_out_of_stock'] = product.stock <= 0
                item['max_available'] = product.stock
                yield item

    def __len__(self):
        """
        Count total items in cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal(self):
        """
        Calculate total sum based on server-side stored products.
        """
        subtotal = Decimal('0.00')
        for item in self:
            subtotal += item['total_price']
        return subtotal
