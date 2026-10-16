from django.db import migrations

from core import seed_data


def seed(apps, schema_editor):
    Category = apps.get_model("core", "Category")
    Product = apps.get_model("core", "Product")
    PromoCode = apps.get_model("core", "PromoCode")
    Review = apps.get_model("core", "Review")

    categories = {}
    for order, (slug, name, tagline, image) in enumerate(seed_data.CATEGORIES):
        categories[slug], _ = Category.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "tagline": tagline,
                "image": seed_data.IMG.format(image),
                "sort_order": order,
            },
        )

    for order, (slug, row) in enumerate(seed_data.PRODUCTS.items()):
        (category, name, price, old_price, rating, reviews, sold, badge,
         image, description, ingredients) = row
        Product.objects.get_or_create(
            slug=slug,
            defaults={
                "category": categories[category],
                "name": name,
                "price": price,
                "old_price": old_price,
                "rating": rating,
                "review_count": reviews,
                "sold_label": sold,
                "badge": badge,
                "image": seed_data.IMG.format(image),
                "description": description,
                "ingredients": ingredients,
                "is_featured": slug in seed_data.FEATURED,
                "is_offer": slug in seed_data.OFFERS,
                "sort_order": order,
            },
        )

    for code, description, percent, min_order, cap in seed_data.PROMO_CODES:
        PromoCode.objects.get_or_create(
            code=code,
            defaults={
                "description": description,
                "discount_percent": percent,
                "min_order": min_order,
                "max_discount": cap,
            },
        )

    if not Review.objects.exists():
        for name, rating, title, comment, product in seed_data.REVIEWS:
            Review.objects.create(
                name=name,
                rating=rating,
                title=title,
                comment=comment,
                product=Product.objects.filter(slug=product).first(),
                is_approved=True,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_menu_orders_reviews"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
