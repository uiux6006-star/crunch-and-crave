from urllib.parse import quote

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import (
    Category,
    ContactMessage,
    Order,
    OrderItem,
    Product,
    PromoCode,
    Review,
)


admin.site.site_header = "Crunch & Crave Admin"
admin.site.site_title = "Crunch & Crave"
admin.site.index_title = "Restaurant dashboard"


# ==========================================================
# MENU
# ==========================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ("name", "tagline", "product_count", "sort_order")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}
    fields = ("name", "slug", "tagline", "image_file", "image", "sort_order")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(n=Count("products"))

    @admin.display(description="Products", ordering="n")
    def product_count(self, obj):
        return obj.n


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "thumbnail",
        "name",
        "category",
        "price",
        "old_price",
        "badge",
        "is_available",
        "is_featured",
        "is_offer",
    )
    list_display_links = ("thumbnail", "name")
    list_editable = ("price", "old_price", "is_available", "is_featured", "is_offer")
    list_filter = ("category", "is_available", "is_featured", "is_offer", "badge")
    search_fields = ("name", "description", "ingredients")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 50
    readonly_fields = ("photo_preview",)
    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "description", "ingredients")}),
        ("Photo", {"fields": ("photo_preview", "image_file", "image")}),
        ("Pricing", {"fields": ("price", "old_price", "badge")}),
        ("Display", {"fields": ("is_available", "is_featured", "is_offer", "sort_order")}),
        ("Social proof", {"fields": ("rating", "review_count", "sold_label")}),
    )

    @admin.display(description="")
    def thumbnail(self, obj):
        return format_html(
            '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:10px">',
            obj.image_url,
        )

    @admin.display(description="Current photo")
    def photo_preview(self, obj):
        if not obj.pk or not obj.image_url:
            return "—"
        return format_html(
            '<img src="{}" style="width:220px;height:170px;object-fit:cover;border-radius:16px">',
            obj.image_url,
        )


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):

    list_display = ("code", "description", "discount_percent", "min_order", "max_discount", "is_active")
    list_editable = ("is_active",)


# ==========================================================
# ORDERS
# ==========================================================

class OrderItemInline(admin.TabularInline):

    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity", "line_total")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


def _status_action(status):
    def action(modeladmin, request, queryset):
        updated = queryset.update(status=status)
        modeladmin.message_user(request, f"{updated} order(s) marked as {status.label}.")
    action.__name__ = f"mark_{status.value}"
    action.short_description = f"Mark selected as “{status.label}”"
    return action


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "order_number",
        "full_name",
        "phone",
        "city",
        "total_display",
        "payment_method",
        "payment_status",
        "status",
        "created_at",
    )
    list_editable = ("payment_status", "status")
    list_filter = ("status", "payment_status", "payment_method", "city", "created_at")
    search_fields = ("order_number", "full_name", "phone", "email", "address", "payment_reference")
    date_hierarchy = "created_at"
    inlines = (OrderItemInline,)
    readonly_fields = (
        "whatsapp_customer",
        "order_number",
        "subtotal",
        "delivery_fee",
        "discount",
        "promo_code",
        "total",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("Order", {"fields": ("order_number", "status", "created_at", "updated_at")}),
        ("Payment", {"fields": ("payment_method", "payment_status", "payment_reference")}),
        ("Customer", {"fields": ("full_name", "phone", "whatsapp_customer", "email")}),
        ("Delivery", {"fields": ("city", "area", "address", "notes")}),
        ("Amounts", {"fields": ("subtotal", "delivery_fee", "discount", "promo_code", "total")}),
    )
    actions = [_status_action(s) for s in Order.Status] + ["mark_paid"]

    @admin.display(description="Total", ordering="total")
    def total_display(self, obj):
        return f"Rs. {obj.total:,}"

    @admin.action(description="Mark payment as received")
    def mark_paid(self, request, queryset):
        updated = queryset.update(payment_status=Order.PaymentStatus.PAID)
        self.message_user(request, f"{updated} order(s) marked as paid.")

    @admin.display(description="WhatsApp")
    def whatsapp_customer(self, obj):
        digits = "".join(ch for ch in obj.phone if ch.isdigit())
        if digits.startswith("0"):
            digits = "92" + digits[1:]
        text = f"Hi {obj.full_name}, this is Crunch & Crave about your order #{obj.order_number}."
        return format_html(
            '<a href="https://wa.me/{}?text={}" target="_blank" rel="noopener" '
            'style="display:inline-flex;gap:8px;align-items:center;padding:8px 16px;border-radius:999px;'
            'background:#25d366;color:#fff;font-weight:700">'
            '<i class="fa-brands fa-whatsapp"></i> Message customer</a>',
            digits,
            quote(text),
        )


# ==========================================================
# REVIEWS & MESSAGES
# ==========================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = ("name", "rating", "title", "product", "is_approved", "created_at")
    list_editable = ("is_approved",)
    list_filter = ("is_approved", "rating", "created_at")
    search_fields = ("name", "title", "comment")
    actions = ("approve",)

    @admin.action(description="Approve selected reviews")
    def approve(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} review(s) approved.")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "email",
        "phone",
        "subject",
        "is_read",
        "created_at",
    )

    list_filter = (
        "is_read",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "phone",
        "subject",
        "message",
    )

    list_editable = (
        "is_read",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )
