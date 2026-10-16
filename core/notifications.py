"""Order notifications: email to the restaurant and the customer."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


logger = logging.getLogger(__name__)


def order_summary_text(order):
    """Plain-text order summary, used by emails and the WhatsApp message."""
    lines = [f"Order #{order.order_number}", ""]
    for item in order.items.all():
        lines.append(f"• {item.quantity} × {item.product_name} — Rs. {item.line_total:,}")
    lines += [
        "",
        f"Subtotal: Rs. {order.subtotal:,}",
        f"Delivery: {'FREE' if not order.delivery_fee else f'Rs. {order.delivery_fee:,}'}",
    ]
    if order.discount:
        lines.append(f"Discount ({order.promo_code}): − Rs. {order.discount:,}")
    lines += [
        f"TOTAL: Rs. {order.total:,}",
        f"Payment: {order.get_payment_method_display()}"
        + (f" (Txn ID: {order.payment_reference})" if order.payment_reference else ""),
        "",
        f"Name: {order.full_name}",
        f"Phone: {order.phone}",
        f"Address: {order.address}, {order.area}, {order.city}",
    ]
    if order.notes:
        lines.append(f"Notes: {order.notes}")
    return "\n".join(lines)


def _send(subject, body, recipients):
    if not recipients:
        return
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients)
    except Exception:  # A mail problem must never break checkout.
        logger.exception("Could not send email: %s", subject)


def notify_new_order(order, request=None):
    admin_link = reverse("admin:core_order_change", args=[order.pk])
    if request is not None:
        admin_link = request.build_absolute_uri(admin_link)

    _send(
        f"🍔 New order #{order.order_number} — Rs. {order.total:,}",
        f"A new order just came in!\n\n{order_summary_text(order)}\n\nOpen in admin: {admin_link}",
        settings.ORDER_NOTIFY_EMAILS,
    )

    if order.email:
        _send(
            f"Your Crunch & Crave order #{order.order_number} is confirmed",
            f"Hi {order.full_name},\n\nThank you for ordering from Crunch & Crave! "
            f"We're preparing your food now.\n\n{order_summary_text(order)}\n\n"
            f"Track your order with your order number and phone at "
            f"{request.build_absolute_uri(reverse('track_order')) if request else '/track/'}\n\n"
            f"— Team Crunch & Crave",
            [order.email],
        )
