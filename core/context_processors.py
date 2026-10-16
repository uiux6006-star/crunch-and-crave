from django.conf import settings

from .cart import Cart
from .models import Category


def site(request):
    return {
        "cart_count": Cart(request).count,
        "nav_categories": Category.objects.all(),
        "site": settings.SITE_INFO,
        "delivery_fee": settings.DELIVERY_FEE,
        "free_delivery_threshold": settings.FREE_DELIVERY_THRESHOLD,
        "demo_mode": settings.DEMO_MODE,
    }
