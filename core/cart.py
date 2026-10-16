"""Session-based shopping cart."""

from django.conf import settings

from .models import Product, PromoCode


MAX_QUANTITY = 20
SESSION_KEY = "cart"
PROMO_SESSION_KEY = "promo_code"


class Cart:

    def __init__(self, request):
        self.session = request.session
        raw = self.session.get(SESSION_KEY, {})
        self.data = {}
        for slug, quantity in raw.items():
            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                continue
            if quantity > 0:
                self.data[slug] = min(quantity, MAX_QUANTITY)

    # ------------------------------------------------------
    # Mutations
    # ------------------------------------------------------

    def _save(self):
        self.session[SESSION_KEY] = self.data
        self.session.modified = True

    def add(self, slug, quantity=1):
        self.data[slug] = min(self.data.get(slug, 0) + quantity, MAX_QUANTITY)
        self._save()

    def set(self, slug, quantity):
        if quantity <= 0:
            self.data.pop(slug, None)
        else:
            self.data[slug] = min(quantity, MAX_QUANTITY)
        self._save()

    def remove(self, slug):
        self.data.pop(slug, None)
        self._save()

    def clear(self):
        self.data = {}
        self.session.pop(PROMO_SESSION_KEY, None)
        self._save()

    def __contains__(self, slug):
        return slug in self.data

    # ------------------------------------------------------
    # Promo code
    # ------------------------------------------------------

    @property
    def promo(self):
        code = self.session.get(PROMO_SESSION_KEY)
        if not code:
            return None
        return PromoCode.objects.filter(code=code, is_active=True).first()

    def set_promo(self, promo):
        if promo:
            self.session[PROMO_SESSION_KEY] = promo.code
        else:
            self.session.pop(PROMO_SESSION_KEY, None)
        self.session.modified = True

    # ------------------------------------------------------
    # Reading
    # ------------------------------------------------------

    @property
    def count(self):
        return sum(self.data.values())

    def items(self):
        """Cart lines with fresh prices from the database.

        Products that were deleted or made unavailable are dropped.
        """
        products = Product.objects.available().select_related("category").in_bulk(
            list(self.data), field_name="slug"
        )
        lines = []
        for slug, quantity in self.data.items():
            product = products.get(slug)
            if product:
                lines.append({
                    "product": product,
                    "quantity": quantity,
                    "total": product.price * quantity,
                })
        return lines

    def summary(self, lines=None):
        if lines is None:
            lines = self.items()

        subtotal = sum(line["total"] for line in lines)

        threshold = settings.FREE_DELIVERY_THRESHOLD
        if subtotal == 0 or subtotal >= threshold:
            delivery_fee = 0
        else:
            delivery_fee = settings.DELIVERY_FEE

        promo = self.promo
        discount = promo.discount_for(subtotal) if promo else 0

        return {
            "lines": lines,
            "count": sum(line["quantity"] for line in lines),
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "discount": discount,
            "promo": promo if discount else None,
            "total": subtotal + delivery_fee - discount,
            "free_delivery_threshold": threshold,
            "free_delivery_remaining": max(threshold - subtotal, 0),
            "free_delivery_progress": min(100, subtotal * 100 // threshold),
        }

    def summary_json(self):
        summary = self.summary()
        return {
            "cart_count": summary["count"],
            "subtotal": summary["subtotal"],
            "delivery_fee": summary["delivery_fee"],
            "discount": summary["discount"],
            "promo": summary["promo"].code if summary["promo"] else None,
            "total": summary["total"],
            "free_delivery_remaining": summary["free_delivery_remaining"],
            "free_delivery_progress": summary["free_delivery_progress"],
            "lines": {
                line["product"].slug: {
                    "quantity": line["quantity"],
                    "total": line["total"],
                }
                for line in summary["lines"]
            },
        }
