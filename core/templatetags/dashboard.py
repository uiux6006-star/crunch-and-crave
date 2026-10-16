"""Live numbers for the admin dashboard (templates/admin/index.html)."""

from datetime import timedelta

from django import template
from django.db.models import Avg, Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from core.models import ContactMessage, Order, OrderItem, Product, Review


register = template.Library()

ACTIVE_STATUSES = [
    Order.Status.PENDING,
    Order.Status.CONFIRMED,
    Order.Status.PREPARING,
    Order.Status.ON_THE_WAY,
]


@register.simple_tag
def dashboard_stats():
    today = timezone.localdate()
    week_start = today - timedelta(days=6)

    valid = Order.objects.exclude(status=Order.Status.CANCELLED)
    totals = valid.aggregate(revenue=Sum("total"), average=Avg("total"), count=Count("id"))
    today_totals = valid.filter(created_at__date=today).aggregate(
        revenue=Sum("total"), count=Count("id")
    )

    # Revenue per day for the last 7 days
    per_day = dict(
        valid.filter(created_at__date__gte=week_start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum("total"))
        .values_list("day", "revenue")
    )
    peak = max(per_day.values(), default=0) or 1
    week = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        revenue = per_day.get(day, 0)
        week.append({
            "label": day.strftime("%a"),
            "date": day,
            "revenue": revenue,
            "percent": round(revenue * 100 / peak) if revenue else 0,
            "is_today": day == today,
        })

    # Orders per status
    status_counts = dict(
        Order.objects.values("status").annotate(n=Count("id")).values_list("status", "n")
    )
    all_orders = sum(status_counts.values())
    statuses = [
        {
            "value": value,
            "label": label,
            "count": status_counts.get(value, 0),
            "percent": round(status_counts.get(value, 0) * 100 / all_orders) if all_orders else 0,
        }
        for value, label in Order.Status.choices
    ]

    top_products = (
        OrderItem.objects.exclude(order__status=Order.Status.CANCELLED)
        .values("product_name")
        .annotate(sold=Sum("quantity"), revenue=Sum(F("unit_price") * F("quantity")))
        .order_by("-sold")[:5]
    )
    top_max = max((p["sold"] for p in top_products), default=0) or 1

    return {
        "revenue": totals["revenue"] or 0,
        "order_count": totals["count"] or 0,
        "average": round(totals["average"] or 0),
        "today_revenue": today_totals["revenue"] or 0,
        "today_orders": today_totals["count"] or 0,
        "active_orders": Order.objects.filter(status__in=ACTIVE_STATUSES).count(),
        "week": week,
        "week_revenue": sum(day["revenue"] for day in week),
        "statuses": statuses,
        "recent_orders": Order.objects.order_by("-created_at")[:6],
        "top_products": [
            dict(p, percent=round(p["sold"] * 100 / top_max)) for p in top_products
        ],
        "products_live": Product.objects.available().count(),
        "products_total": Product.objects.count(),
        "pending_reviews": Review.objects.filter(is_approved=False).count(),
        "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
    }
