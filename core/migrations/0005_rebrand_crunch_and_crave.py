"""Rebrand N.J Fastfood → Crunch & Crave in existing menu data."""

from django.db import migrations


SLUGS = {
    "nj-special-burger": "crave-special-burger",
    "nj-mega-deal": "crave-mega-deal",
}

TEXT = [
    ("N.J Special Burger", "Crave Special Burger"),
    ("N.J Mega Deal", "Crave Mega Deal"),
    ("N.J Special Sauce", "Crave Special Sauce"),
    ("N.J special sauce", "Crave special sauce"),
    ("signature N.J sauce", "signature Crave sauce"),
    ("The ultimate N.J feast", "The ultimate Crunch & Crave feast"),
    ("N.J Fastfood", "Crunch & Crave"),
]


def replace_all(value):
    for old, new in TEXT:
        value = value.replace(old, new)
    return value


def rebrand(apps, schema_editor):
    Product = apps.get_model("core", "Product")
    PromoCode = apps.get_model("core", "PromoCode")
    Review = apps.get_model("core", "Review")

    for old, new in SLUGS.items():
        if not Product.objects.filter(slug=new).exists():
            Product.objects.filter(slug=old).update(slug=new)

    for product in Product.objects.all():
        fields = {
            "name": replace_all(product.name),
            "description": replace_all(product.description),
            "ingredients": replace_all(product.ingredients),
        }
        if any(getattr(product, k) != v for k, v in fields.items()):
            Product.objects.filter(pk=product.pk).update(**fields)

    if not PromoCode.objects.filter(code="CRAVE10").exists():
        PromoCode.objects.filter(code="NJ10").update(code="CRAVE10")

    for review in Review.objects.all():
        title, comment = replace_all(review.title), replace_all(review.comment)
        if (title, comment) != (review.title, review.comment):
            Review.objects.filter(pk=review.pk).update(title=title, comment=comment)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_uploads_payments"),
    ]

    operations = [
        migrations.RunPython(rebrand, migrations.RunPython.noop),
    ]
