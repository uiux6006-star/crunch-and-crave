# ==========================================================
# CRUNCH & CRAVE - VIEWS
# ==========================================================

from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .cart import MAX_QUANTITY, Cart
from .forms import CheckoutForm, ContactForm, ReviewForm, TrackOrderForm
from .models import Category, Order, OrderItem, Product, PromoCode, Review
from .notifications import notify_new_order, order_summary_text
from .spam import rate_limited


RATE_LIMIT_MESSAGE = "Too many attempts from your connection. Please try again in a few minutes."


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _review_stats():
    approved = Review.objects.filter(is_approved=True)
    stats = approved.aggregate(average=Avg("rating"), total=Count("id"))
    counts = dict(
        approved.values_list("rating").annotate(n=Count("id")).values_list("rating", "n")
    )
    total = stats["total"] or 0
    breakdown = [
        {
            "stars": stars,
            "count": counts.get(stars, 0),
            "percent": round(counts.get(stars, 0) * 100 / total) if total else 0,
        }
        for stars in range(5, 0, -1)
    ]
    return {
        "average": round(stats["average"] or 0, 1),
        "total": total,
        "breakdown": breakdown,
    }


# ==========================================================
# PAGES
# ==========================================================

def home(request):
    return render(request, "home.html", {
        "categories": Category.objects.annotate(
            item_count=Count("products", filter=Q(products__is_available=True))
        ),
        "featured": Product.objects.available().filter(is_featured=True)
            .select_related("category")[:8],
        "product_total": Product.objects.available().count(),
        "combo": Product.objects.available().filter(slug="zinger-burger-fries-drink").first(),
        "reviews": Review.objects.filter(is_approved=True)[:3],
        "review_stats": _review_stats(),
    })


def menu(request):
    query = request.GET.get("search", "").strip()
    category_slug = request.GET.get("category", "")

    products = Product.objects.available().select_related("category")
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    return render(request, "menu.html", {
        "products": products,
        "categories": Category.objects.filter(products__in=products).distinct(),
        "query": query,
        "active_category": category_slug,
    })


def product_detail(request, slug=None):
    # Old links used /product/?product=<slug>
    if slug is None:
        legacy = request.GET.get("product")
        if legacy:
            return redirect("product_detail", slug=legacy, permanent=True)
        return redirect("menu")

    # Products renamed in the Crunch & Crave rebrand keep their old links working.
    renamed = {"nj-special-burger": "crave-special-burger", "nj-mega-deal": "crave-mega-deal"}
    if slug in renamed:
        return redirect("product_detail", slug=renamed[slug], permanent=True)

    product = get_object_or_404(
        Product.objects.available().select_related("category"), slug=slug
    )
    return render(request, "product-detail.html", {
        "product": product,
        "related": Product.objects.available()
            .filter(category=product.category)
            .exclude(pk=product.pk)[:4],
        "product_reviews": product.customer_reviews.filter(is_approved=True)[:4],
        "in_cart": Cart(request).data.get(product.slug, 0),
    })


def offers(request):
    return render(request, "offers.html", {
        "offers_products": Product.objects.available().filter(is_offer=True),
        "promo_codes": PromoCode.objects.filter(is_active=True),
    })


def about(request):
    return render(request, "about.html", {
        "product_total": Product.objects.available().count(),
        "review_stats": _review_stats(),
    })


def gallery(request):
    return render(request, "gallery.html", {
        "items": Product.objects.available().select_related("category"),
        "categories": Category.objects.all(),
    })


def reviews(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid() and rate_limited(request, "review"):
            messages.error(request, RATE_LIMIT_MESSAGE)
            return redirect("reviews")
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thank you! Your review will appear once our team approves it.",
            )
            return redirect("reviews")
        messages.error(request, "Please fix the highlighted fields.")
    else:
        form = ReviewForm()

    return render(request, "reviews.html", {
        "form": form,
        "reviews": Review.objects.filter(is_approved=True).select_related("product"),
        "review_stats": _review_stats(),
    })


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid() and rate_limited(request, "contact"):
            messages.error(request, RATE_LIMIT_MESSAGE)
            return redirect("contact")
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your message has been sent! Our team will contact you soon.",
            )
            return redirect("contact")
        messages.error(request, "Please fill in all required fields correctly.")
    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})


# ==========================================================
# CART
# ==========================================================

def cart(request):
    cart = Cart(request)
    return render(request, "cart.html", {
        "summary": cart.summary(),
        "suggestions": Product.objects.available()
            .filter(category__slug__in=["drinks", "fries"])
            .exclude(slug__in=list(cart.data))[:4],
    })


def _cart_response(cart, message, status=200, success=True):
    data = cart.summary_json()
    data.update(success=success, message=message)
    return JsonResponse(data, status=status)


@require_POST
def add_to_cart(request):
    slug = request.POST.get("product") or request.POST.get("product_slug")
    product = Product.objects.available().filter(slug=slug).first()
    cart = Cart(request)

    if not product:
        return _cart_response(cart, "Product not found.", 404, False)

    quantity = max(1, min(_int(request.POST.get("quantity"), 1), MAX_QUANTITY))
    cart.add(product.slug, quantity)
    return _cart_response(cart, f"{product.name} added to cart.")


@require_POST
def update_cart(request):
    slug = request.POST.get("product") or request.POST.get("product_slug")
    cart = Cart(request)

    if slug not in cart:
        return _cart_response(cart, "Product is not in cart.", 404, False)

    cart.set(slug, _int(request.POST.get("quantity"), 1))
    return _cart_response(cart, "Cart updated.")


@require_POST
def remove_from_cart(request, product_slug):
    cart = Cart(request)
    cart.remove(product_slug)
    return _cart_response(cart, "Item removed from cart.")


@require_POST
def clear_cart(request):
    cart = Cart(request)
    cart.clear()
    return _cart_response(cart, "Cart cleared.")


@require_POST
def apply_promo(request):
    cart = Cart(request)
    code = request.POST.get("code", "").strip().upper()

    if not code:
        cart.set_promo(None)
        return _cart_response(cart, "Promo code removed.")

    promo = PromoCode.objects.filter(code=code, is_active=True).first()
    if not promo:
        return _cart_response(cart, "Invalid promo code.", 400, False)

    subtotal = cart.summary()["subtotal"]
    if subtotal < promo.min_order:
        return _cart_response(
            cart,
            f"{promo.code} needs a minimum order of Rs. {promo.min_order:,}.",
            400,
            False,
        )

    cart.set_promo(promo)
    return _cart_response(cart, f"{promo.code} applied!")


# ==========================================================
# CHECKOUT & ORDERS
# ==========================================================

def checkout(request):
    cart = Cart(request)
    summary = cart.summary()

    if not summary["lines"]:
        messages.info(request, "Your cart is empty. Add something delicious first!")
        return redirect("menu")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid() and rate_limited(request, "checkout"):
            messages.error(request, RATE_LIMIT_MESSAGE)
            return redirect("checkout")
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if order.payment_method in Order.ONLINE_PAYMENTS:
                    order.payment_status = Order.PaymentStatus.AWAITING
                order.subtotal = summary["subtotal"]
                order.delivery_fee = summary["delivery_fee"]
                order.discount = summary["discount"]
                order.total = summary["total"]
                order.promo_code = summary["promo"].code if summary["promo"] else ""
                order.save()
                OrderItem.objects.bulk_create([
                    OrderItem(
                        order=order,
                        product=line["product"],
                        product_name=line["product"].name,
                        unit_price=line["product"].price,
                        quantity=line["quantity"],
                    )
                    for line in summary["lines"]
                ])
                transaction.on_commit(lambda: notify_new_order(order, request))
            cart.clear()
            request.session.setdefault("my_orders", [])
            request.session["my_orders"] = (
                [order.order_number] + request.session["my_orders"]
            )[:10]
            return redirect(order)
    else:
        form = CheckoutForm()

    return render(request, "checkout.html", {
        "form": form,
        "summary": summary,
        "payment_accounts": settings.PAYMENT_ACCOUNTS,
    })


def order_success(request, order_number):
    # Only the browser that placed the order can view it here;
    # anyone else must use the tracking form with the phone number.
    if order_number not in request.session.get("my_orders", []):
        return redirect("track_order")
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), order_number=order_number
    )
    whatsapp_text = "Hi Crunch & Crave! I just placed an order:\n\n" + order_summary_text(order)
    return render(request, "order_success.html", {
        "order": order,
        "whatsapp_url": f"https://wa.me/{settings.SITE_INFO['whatsapp']}?text={quote(whatsapp_text)}",
    })


def track_order(request):
    order = None
    form = TrackOrderForm(request.GET or None)

    if form.is_valid():
        digits = "".join(ch for ch in form.cleaned_data["phone"] if ch.isdigit())
        candidate = (
            Order.objects.prefetch_related("items")
            .filter(order_number=form.cleaned_data["order_number"])
            .first()
        )
        if candidate and "".join(ch for ch in candidate.phone if ch.isdigit())[-10:] == digits[-10:]:
            order = candidate
        else:
            messages.error(request, "No order found with that number and phone.")

    recent = Order.objects.filter(
        order_number__in=request.session.get("my_orders", [])
    )[:5]

    return render(request, "order_tracking.html", {
        "form": form,
        "order": order,
        "recent_orders": recent,
    })


# ==========================================================
# LEGAL PAGES
# ==========================================================

def privacy(request):
    return render(request, "legal/privacy.html")


def terms(request):
    return render(request, "legal/terms.html")


# ==========================================================
# ADMIN — LIVE NEW-ORDER ALERTS
# ==========================================================

@staff_member_required
def admin_order_feed(request):
    """Orders newer than ?after=<id>, polled by the admin to show alerts."""
    after = _int(request.GET.get("after"), 0)
    latest = Order.objects.order_by("-pk").first()
    new_orders = Order.objects.filter(pk__gt=after).order_by("pk")[:10] if after else []

    return JsonResponse({
        "latest_id": latest.pk if latest else 0,
        "active": Order.objects.filter(status__in=[
            Order.Status.PENDING, Order.Status.CONFIRMED,
            Order.Status.PREPARING, Order.Status.ON_THE_WAY,
        ]).count(),
        "orders": [
            {
                "id": order.pk,
                "number": order.order_number,
                "name": order.full_name,
                "total": order.total,
                "url": reverse("admin:core_order_change", args=[order.pk]),
            }
            for order in new_orders
        ],
    })
