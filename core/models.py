import secrets

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


# ==========================================================
# MENU
# ==========================================================

class Category(models.Model):

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    tagline = models.CharField(max_length=80, blank=True)
    image_file = models.ImageField(
        "image",
        upload_to="categories/",
        blank=True,
        help_text="Upload a photo (recommended), or paste a link below",
    )
    image = models.URLField("image link", max_length=500, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        return self.image_file.url if self.image_file else self.image


class ProductQuerySet(models.QuerySet):

    def available(self):
        return self.filter(is_available=True)


class Product(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    price = models.PositiveIntegerField(help_text="Price in PKR")
    old_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Shown crossed out when higher than the price",
    )
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=4.5,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    review_count = models.PositiveIntegerField(default=0)
    sold_label = models.CharField(max_length=20, blank=True)
    badge = models.CharField(max_length=30, blank=True)
    image_file = models.ImageField(
        "photo",
        upload_to="products/",
        blank=True,
        help_text="Upload a photo from your computer (recommended)",
    )
    image = models.URLField(
        "photo link",
        max_length=500,
        blank=True,
        help_text="…or paste an image link instead",
    )
    description = models.TextField()
    ingredients = models.CharField(max_length=300, blank=True)

    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(
        default=False,
        help_text="Show on the home page",
    )
    is_offer = models.BooleanField(
        default=False,
        help_text="Show on the offers page",
    )
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ("category__sort_order", "sort_order", "name")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.slug])

    def clean(self):
        if not self.image_file and not self.image:
            raise ValidationError("Upload a photo or paste a photo link.")

    @property
    def image_url(self):
        return self.image_file.url if self.image_file else self.image

    @property
    def has_discount(self):
        return bool(self.old_price and self.old_price > self.price)

    @property
    def discount_percent(self):
        if not self.has_discount:
            return 0
        return round((self.old_price - self.price) * 100 / self.old_price)

    @property
    def ingredient_list(self):
        return [i.strip() for i in self.ingredients.split(",") if i.strip()]


# ==========================================================
# PROMO CODES
# ==========================================================

class PromoCode(models.Model):

    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=120, blank=True)
    discount_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(90)],
    )
    min_order = models.PositiveIntegerField(default=0)
    max_discount = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional cap on the discount amount (PKR)",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def discount_for(self, subtotal):
        if not self.is_active or subtotal < self.min_order:
            return 0
        amount = subtotal * self.discount_percent // 100
        if self.max_discount:
            amount = min(amount, self.max_discount)
        return amount


# ==========================================================
# ORDERS
# ==========================================================

def generate_order_number():
    return "CC" + secrets.token_hex(3).upper()


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Order Placed"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        ON_THE_WAY = "on_the_way", "On The Way"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class Payment(models.TextChoices):
        COD = "cod", "Cash on Delivery"
        JAZZCASH = "jazzcash", "JazzCash"
        EASYPAISA = "easypaisa", "EasyPaisa"
        BANK = "bank", "Bank Transfer"

    class PaymentStatus(models.TextChoices):
        ON_DELIVERY = "on_delivery", "Pay on delivery"
        AWAITING = "awaiting", "Awaiting verification"
        PAID = "paid", "Paid"
        REJECTED = "rejected", "Payment rejected"

    ONLINE_PAYMENTS = [Payment.JAZZCASH, Payment.EASYPAISA, Payment.BANK]

    TRACKING_STEPS = [
        Status.PENDING,
        Status.CONFIRMED,
        Status.PREPARING,
        Status.ON_THE_WAY,
        Status.DELIVERED,
    ]

    order_number = models.CharField(
        max_length=12,
        unique=True,
        default=generate_order_number,
        editable=False,
    )

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=60)
    area = models.CharField(max_length=100)
    address = models.TextField()
    notes = models.CharField(max_length=300, blank=True)

    payment_method = models.CharField(
        max_length=20,
        choices=Payment.choices,
        default=Payment.COD,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.ON_DELIVERY,
    )
    payment_reference = models.CharField(
        "transaction ID",
        max_length=40,
        blank=True,
        help_text="Transaction ID the customer gave for an online payment",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    subtotal = models.PositiveIntegerField()
    delivery_fee = models.PositiveIntegerField(default=0)
    discount = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField()
    promo_code = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"#{self.order_number} — {self.full_name}"

    def get_absolute_url(self):
        return reverse("order_success", args=[self.order_number])

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def tracking_steps(self):
        """Each step with a done/current flag, for the tracking timeline."""
        if self.status == self.Status.CANCELLED:
            return []
        current = self.TRACKING_STEPS.index(self.status)
        return [
            {
                "label": step.label,
                "done": index <= current,
                "current": index == current,
            }
            for index, step in enumerate(self.TRACKING_STEPS)
        ]


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # Snapshots, so later menu edits never change a past order.
    product_name = models.CharField(max_length=120)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


# ==========================================================
# REVIEWS
# ==========================================================

class Review(models.Model):

    name = models.CharField(max_length=80)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    title = models.CharField(max_length=100, blank=True)
    comment = models.TextField(max_length=1000)
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_reviews",
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Only approved reviews are shown on the site",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} — {self.rating}★"

    @property
    def initial(self):
        return self.name[:1].upper()


# ==========================================================
# CONTACT
# ==========================================================

class ContactMessage(models.Model):

    name = models.CharField(
        max_length=100
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    subject = models.CharField(
        max_length=200
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.name} - {self.subject}"
