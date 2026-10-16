import re

from django.contrib.staticfiles import finders
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, ContactMessage, Order, Product, PromoCode, Review
from .spam import make_token


@override_settings(SPAM_MIN_SECONDS=0)
class NJTestCase(TestCase):
    """Clears rate-limit counters and skips the human-speed check."""

    def setUp(self):
        super().setUp()
        cache.clear()


class SeedDataTests(NJTestCase):

    def test_menu_is_seeded(self):
        self.assertEqual(Category.objects.count(), 8)
        self.assertGreaterEqual(Product.objects.count(), 38)
        self.assertTrue(Product.objects.filter(is_featured=True).exists())
        self.assertTrue(Product.objects.filter(is_offer=True).exists())
        self.assertTrue(PromoCode.objects.filter(code="CRAVE10").exists())


class PageTests(NJTestCase):

    PAGES = [
        "home", "menu", "offers", "about", "gallery",
        "reviews", "contact", "cart", "track_order",
    ]

    def test_pages_render(self):
        for name in self.PAGES:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_every_static_reference_exists(self):
        for name in self.PAGES:
            html = self.client.get(reverse(name)).content.decode()
            for path in re.findall(r'(?:href|src)="/static/([^"]+)"', html):
                with self.subTest(page=name, file=path):
                    self.assertIsNotNone(finders.find(path))

    def test_product_detail(self):
        response = self.client.get(reverse("product_detail", args=["zinger-burger"]))
        self.assertContains(response, "Zinger Burger")
        self.assertContains(response, 'data-add="zinger-burger"')

    def test_unknown_product_404(self):
        response = self.client.get(reverse("product_detail", args=["nope"]))
        self.assertEqual(response.status_code, 404)

    def test_unavailable_product_hidden(self):
        Product.objects.filter(slug="pepsi").update(is_available=False)
        self.assertEqual(self.client.get("/product/pepsi/").status_code, 404)
        self.assertNotContains(self.client.get(reverse("menu")), 'data-add="pepsi"')

    def test_legacy_product_url_redirects(self):
        response = self.client.get("/product/?product=zinger-burger")
        self.assertRedirects(response, "/product/zinger-burger/", status_code=301)

    def test_menu_search(self):
        response = self.client.get(reverse("menu"), {"search": "shawarma"})
        self.assertContains(response, "Zinger Shawarma")
        self.assertNotContains(response, 'data-add="pepsi"')

    def test_home_add_buttons_are_wired(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "data-add=")


class CartTests(NJTestCase):

    def add(self, slug, quantity=1):
        return self.client.post(reverse("add_to_cart"), {"product": slug, "quantity": quantity})

    def test_add_and_totals(self):
        data = self.add("zinger-burger", 2).json()
        self.assertTrue(data["success"])
        self.assertEqual(data["cart_count"], 2)
        self.assertEqual(data["subtotal"], 1198)
        self.assertEqual(data["delivery_fee"], 200)
        self.assertEqual(data["total"], 1398)

    def test_free_delivery_over_threshold(self):
        data = self.add("crave-mega-deal").json()
        self.assertEqual(data["delivery_fee"], 0)
        self.assertEqual(data["total"], 1999)

    def test_quantity_capped(self):
        self.add("pepsi", 15)
        data = self.add("pepsi", 15).json()
        self.assertEqual(data["cart_count"], 20)

    def test_add_requires_post(self):
        self.assertEqual(self.client.get(reverse("add_to_cart")).status_code, 405)

    def test_add_unknown_product(self):
        self.assertEqual(self.add("does-not-exist").status_code, 404)

    def test_update_and_remove(self):
        self.add("pepsi")
        data = self.client.post(reverse("update_cart"), {"product": "pepsi", "quantity": 5}).json()
        self.assertEqual(data["lines"]["pepsi"]["quantity"], 5)

        data = self.client.post(reverse("remove_from_cart", args=["pepsi"])).json()
        self.assertEqual(data["cart_count"], 0)

    def test_remove_requires_post(self):
        self.add("pepsi")
        self.assertEqual(self.client.get(reverse("remove_from_cart", args=["pepsi"])).status_code, 405)

    def test_clear(self):
        self.add("pepsi")
        data = self.client.post(reverse("clear_cart")).json()
        self.assertEqual(data["cart_count"], 0)

    def test_cart_page_shows_items(self):
        self.add("zinger-burger", 3)
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "Zinger Burger")
        self.assertContains(response, "Rs. 1,797")

    def test_header_count(self):
        self.add("pepsi", 3)
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'data-count="3"')

    def test_promo_code(self):
        self.add("zinger-burger", 2)  # 1198
        data = self.client.post(reverse("apply_promo"), {"code": "crave10"}).json()
        self.assertTrue(data["success"])
        self.assertEqual(data["discount"], 119)
        self.assertEqual(data["total"], 1198 + 200 - 119)

    def test_promo_min_order(self):
        self.add("pepsi")
        response = self.client.post(reverse("apply_promo"), {"code": "WELCOME20"})
        self.assertEqual(response.status_code, 400)

    def test_invalid_promo(self):
        self.add("pepsi")
        response = self.client.post(reverse("apply_promo"), {"code": "FAKE"})
        self.assertEqual(response.status_code, 400)


class CheckoutTests(NJTestCase):

    VALID = {
        "full_name": "Ali Khan",
        "phone": "0300 1234567",
        "email": "",
        "city": "Lahore",
        "area": "Gulberg",
        "address": "House 1, Street 2",
        "notes": "Extra spicy",
        "payment_method": "cod",
        "form_ts": make_token(),
    }

    def setUp(self):
        super().setUp()
        self.client.post(reverse("add_to_cart"), {"product": "zinger-burger", "quantity": 2})
        self.client.post(reverse("add_to_cart"), {"product": "pepsi", "quantity": 1})

    def test_empty_cart_redirects_to_menu(self):
        self.client.post(reverse("clear_cart"))
        self.assertRedirects(self.client.get(reverse("checkout")), reverse("menu"))

    def test_checkout_page_shows_summary(self):
        response = self.client.get(reverse("checkout"))
        self.assertContains(response, "Zinger Burger")
        self.assertContains(response, "Rs. 1,518")

    def test_place_order(self):
        response = self.client.post(reverse("checkout"), self.VALID)
        order = Order.objects.get()
        self.assertRedirects(response, order.get_absolute_url())

        self.assertEqual(order.subtotal, 1318)
        self.assertEqual(order.delivery_fee, 200)
        self.assertEqual(order.total, 1518)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.status, Order.Status.PENDING)

        # Cart is emptied
        self.assertEqual(self.client.get(reverse("cart")).context["summary"]["count"], 0)

        # Confirmation page
        page = self.client.get(order.get_absolute_url())
        self.assertContains(page, order.order_number)
        self.assertContains(page, "Extra spicy")

    def test_order_with_promo(self):
        self.client.post(reverse("apply_promo"), {"code": "CRAVE10"})
        self.client.post(reverse("checkout"), self.VALID)
        order = Order.objects.get()
        self.assertEqual(order.discount, 131)
        self.assertEqual(order.promo_code, "CRAVE10")
        self.assertEqual(order.total, 1318 + 200 - 131)

    def test_prices_come_from_database(self):
        Product.objects.filter(slug="pepsi").update(price=100)
        self.client.post(reverse("checkout"), self.VALID)
        self.assertEqual(Order.objects.get().subtotal, 1298)

    def test_invalid_checkout_shows_errors(self):
        data = dict(self.VALID, phone="12", full_name="")
        response = self.client.post(reverse("checkout"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid phone number")
        self.assertFalse(Order.objects.exists())

    def test_other_browser_cannot_view_confirmation(self):
        self.client.post(reverse("checkout"), self.VALID)
        order = Order.objects.get()
        self.client.logout()
        self.client.cookies.clear()
        response = self.client.get(order.get_absolute_url())
        self.assertRedirects(response, reverse("track_order"))

    def test_tracking(self):
        self.client.post(reverse("checkout"), self.VALID)
        order = Order.objects.get()
        order.status = Order.Status.PREPARING
        order.save()

        response = self.client.get(reverse("track_order"), {
            "order_number": order.order_number.lower(),
            "phone": "+92 300 1234567",
        })
        self.assertEqual(response.context["order"], order)
        self.assertContains(response, "Preparing")

        wrong = self.client.get(reverse("track_order"), {
            "order_number": order.order_number,
            "phone": "0311 0000000",
        })
        self.assertIsNone(wrong.context["order"])

    def test_tracking_steps(self):
        order = Order(status=Order.Status.ON_THE_WAY)
        steps = order.tracking_steps
        self.assertEqual([s["done"] for s in steps], [True, True, True, True, False])
        self.assertTrue(steps[3]["current"])
        self.assertEqual(Order(status=Order.Status.CANCELLED).tracking_steps, [])


class ReviewTests(NJTestCase):

    def test_submitted_review_needs_approval(self):
        response = self.client.post(reverse("reviews"), {
            "name": "Test User",
            "rating": 4,
            "title": "Nice",
            "comment": "Really good fries",
            "product": "",
            "form_ts": make_token(),
        })
        self.assertRedirects(response, reverse("reviews"))
        review = Review.objects.get(name="Test User")
        self.assertFalse(review.is_approved)
        self.assertNotContains(self.client.get(reverse("reviews")), "Really good fries")

        review.is_approved = True
        review.save()
        self.assertContains(self.client.get(reverse("reviews")), "Really good fries")

    def test_invalid_review(self):
        response = self.client.post(reverse("reviews"), {"name": "", "rating": 9, "comment": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Review.objects.filter(rating=9).exists())


class AdminDashboardTests(NJTestCase):

    def setUp(self):
        super().setUp()
        from django.contrib.auth.models import User
        self.admin = User.objects.create_superuser("boss", password="pass12345")
        self.client.force_login(self.admin)

    def test_dashboard_empty(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nja-dash")
        self.assertContains(response, "No orders yet")

    def test_dashboard_with_orders(self):
        order = Order.objects.create(
            full_name="Ali", phone="03001234567", city="Lahore", area="X",
            address="Y", subtotal=1000, delivery_fee=200, total=1200,
        )
        order.items.create(product_name="Zinger Burger", unit_price=500, quantity=2)
        Order.objects.create(
            full_name="Cancelled", phone="03001234567", city="Lahore", area="X",
            address="Y", subtotal=900, total=900, status=Order.Status.CANCELLED,
        )

        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, 'data-count="1200"')
        self.assertContains(response, "Zinger Burger")
        self.assertContains(response, order.order_number)

    def test_admin_pages_render(self):
        for name in ["order", "product", "review", "category", "promocode", "contactmessage"]:
            with self.subTest(model=name):
                response = self.client.get(reverse(f"admin:core_{name}_changelist"))
                self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        self.client.logout()
        response = self.client.get(reverse("admin:login"))
        self.assertContains(response, "nj-admin.css")


class ContactTests(NJTestCase):

    def test_contact_saves_message(self):
        response = self.client.post(reverse("contact"), {
            "name": "Sara",
            "email": "sara@example.com",
            "phone": "",
            "subject": "Catering",
            "message": "Party of 30",
            "form_ts": make_token(),
        })
        self.assertRedirects(response, reverse("contact"))
        self.assertTrue(ContactMessage.objects.filter(subject="Catering").exists())

    def test_contact_rejects_bad_email(self):
        response = self.client.post(reverse("contact"), {
            "name": "Sara", "email": "not-an-email", "subject": "x", "message": "y",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ContactMessage.objects.exists())


class SpamProtectionTests(NJTestCase):

    def contact_data(self, **extra):
        data = {
            "name": "Sara", "email": "sara@example.com", "phone": "",
            "subject": "Hello", "message": "Hi there", "form_ts": make_token(),
        }
        data.update(extra)
        return data

    def test_honeypot_blocks_bots(self):
        response = self.client.post(reverse("contact"), self.contact_data(hp_contact="http://spam.example"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "looked automated")
        self.assertFalse(ContactMessage.objects.exists())

    def test_missing_timestamp_rejected(self):
        response = self.client.post(reverse("contact"), self.contact_data(form_ts=""))
        self.assertContains(response, "form expired")
        self.assertFalse(ContactMessage.objects.exists())

    @override_settings(SPAM_MIN_SECONDS=30)
    def test_too_fast_rejected(self):
        response = self.client.post(reverse("contact"), self.contact_data())
        self.assertContains(response, "looked automated")
        self.assertFalse(ContactMessage.objects.exists())

    @override_settings(RATE_LIMITS={"contact": (2, 600), "review": (3, 600), "checkout": (5, 600)})
    def test_rate_limit(self):
        for _ in range(3):
            self.client.post(reverse("contact"), self.contact_data())
        self.assertEqual(ContactMessage.objects.count(), 2)

    def test_forms_render_hidden_fields(self):
        for name in ["contact", "reviews"]:
            with self.subTest(page=name):
                html = self.client.get(reverse(name)).content.decode()
                self.assertIn('name="hp_contact"', html)
                self.assertIn('name="form_ts" value="', html)


class PaymentAndNotificationTests(NJTestCase):

    def setUp(self):
        super().setUp()
        self.client.post(reverse("add_to_cart"), {"product": "zinger-burger", "quantity": 1})
        self.data = dict(CheckoutTests.VALID, email="customer@example.com", form_ts=make_token())

    def place(self, **extra):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse("checkout"), dict(self.data, **extra))

    def test_cod_order_emails_restaurant_and_customer(self):
        self.place()
        order = Order.objects.get()
        self.assertEqual(order.payment_status, Order.PaymentStatus.ON_DELIVERY)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(order.order_number, mail.outbox[0].subject)
        self.assertIn("Zinger Burger", mail.outbox[0].body)
        self.assertEqual(mail.outbox[1].to, ["customer@example.com"])

    def test_online_payment_needs_transaction_id(self):
        response = self.place(payment_method="jazzcash", payment_reference="")
        self.assertContains(response, "transaction ID")
        self.assertFalse(Order.objects.exists())

    def test_online_payment_awaits_verification(self):
        self.place(payment_method="easypaisa", payment_reference="TX998877")
        order = Order.objects.get()
        self.assertEqual(order.payment_status, Order.PaymentStatus.AWAITING)
        self.assertEqual(order.payment_reference, "TX998877")
        page = self.client.get(order.get_absolute_url())
        self.assertContains(page, "Payment being verified")

    def test_cod_ignores_transaction_id(self):
        self.place(payment_reference="SHOULD-NOT-SAVE")
        self.assertEqual(Order.objects.get().payment_reference, "")

    def test_whatsapp_button(self):
        self.place()
        page = self.client.get(Order.objects.get().get_absolute_url())
        self.assertContains(page, "https://wa.me/")
        self.assertContains(page, "Zinger%20Burger")

    def test_checkout_shows_payment_accounts(self):
        response = self.client.get(reverse("checkout"))
        self.assertContains(response, 'value="jazzcash"')
        self.assertContains(response, 'value="easypaisa"')
        self.assertContains(response, "0323 8144826")
        self.assertContains(response, 'value="bank"')
        self.assertContains(response, "PK36 SCBL 0000 0011 2345 6702")

    def test_unconfigured_payment_method_rejected(self):
        from django.conf import settings
        accounts = {k: v for k, v in settings.PAYMENT_ACCOUNTS.items() if k != "bank"}
        with self.settings(PAYMENT_ACCOUNTS=accounts):
            response = self.place(payment_method="bank", payment_reference="TX123456")
        self.assertContains(response, "isn&#x27;t available")
        self.assertFalse(Order.objects.exists())

    def test_contact_number_on_site(self):
        html = self.client.get(reverse("contact")).content.decode()
        self.assertIn("0323-8144826", html)
        self.assertIn("wa.me/923238144826", html)
        self.assertIn("tel:+923238144826", html)


class LegalAndUploadTests(NJTestCase):

    def test_legal_pages(self):
        for name, text in [("privacy", "Privacy"), ("terms", "Terms")]:
            with self.subTest(page=name):
                self.assertContains(self.client.get(reverse(name)), text)
        self.assertContains(self.client.get(reverse("home")), reverse("privacy"))

    def test_uploaded_photo_wins_over_link(self):
        product = Product.objects.get(slug="pepsi")
        self.assertTrue(product.image_url.startswith("https://"))
        product.image_file = "products/pepsi.jpg"
        product.save()
        self.assertEqual(product.image_url, "/media/products/pepsi.jpg")
        self.assertContains(self.client.get(reverse("menu")), "/media/products/pepsi.jpg")

    def test_product_needs_some_photo(self):
        from django.core.exceptions import ValidationError
        product = Product(name="X", slug="x", price=1, description="d", category=Category.objects.first())
        with self.assertRaises(ValidationError):
            product.full_clean()


class AdminOrderFeedTests(NJTestCase):

    def test_staff_only(self):
        response = self.client.get(reverse("admin_order_feed"))
        self.assertEqual(response.status_code, 302)

    def test_feed_returns_new_orders(self):
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.create_superuser("boss", password="pass12345"))
        first = Order.objects.create(full_name="A", phone="0300", city="L", area="X", address="Y", subtotal=1, total=1)
        second = Order.objects.create(full_name="B", phone="0300", city="L", area="X", address="Y", subtotal=5, total=5)

        data = self.client.get(reverse("admin_order_feed"), {"after": first.pk}).json()
        self.assertEqual(data["latest_id"], second.pk)
        self.assertEqual([o["number"] for o in data["orders"]], [second.order_number])
        self.assertEqual(data["active"], 2)

        self.assertEqual(self.client.get(reverse("admin_order_feed")).json()["orders"], [])


class BrandTests(NJTestCase):

    def test_new_brand_everywhere(self):
        for name in ["home", "menu", "about", "contact", "privacy"]:
            with self.subTest(page=name):
                html = self.client.get(reverse(name)).content.decode()
                self.assertIn("Crunch <em>&amp;</em> Crave", html)
                self.assertIn("img/logo-mark.svg", html)
                self.assertNotIn("N.J", html)

    def test_admin_brand(self):
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.create_superuser("boss", password="pass12345"))
        html = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("Crunch &amp; Crave", html)
        self.assertNotIn("N.J", html)

    def test_old_product_links_redirect(self):
        response = self.client.get("/product/nj-special-burger/")
        self.assertRedirects(response, "/product/crave-special-burger/", status_code=301)

    def test_new_order_numbers(self):
        order = Order.objects.create(full_name="A", phone="0300", city="L", area="X", address="Y", subtotal=1, total=1)
        self.assertTrue(order.order_number.startswith("CC"))


class DemoAndProductionTests(NJTestCase):

    def test_demo_banner_on(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Portfolio demo")
        self.assertContains(response, 'class="has-demo"')

    def test_demo_warning_at_checkout(self):
        self.client.post(reverse("add_to_cart"), {"product": "pepsi"})
        self.assertContains(self.client.get(reverse("checkout")), "Please don't send real money")

    @override_settings(DEMO_MODE=False)
    def test_demo_banner_off(self):
        self.assertNotContains(self.client.get(reverse("home")), "Portfolio demo")

    def test_custom_404(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "got eaten", status_code=404)

    def test_500_template_is_self_contained(self):
        from django.template.loader import render_to_string
        html = render_to_string("500.html")
        self.assertIn("slipped up", html)


class EnsureAdminCommandTests(NJTestCase):

    def run_command(self, **env):
        import os
        from io import StringIO
        from unittest import mock
        from django.core.management import call_command
        out = StringIO()
        with mock.patch.dict(os.environ, env, clear=False):
            call_command("ensure_admin", stdout=out)
        return out.getvalue()

    def test_creates_then_updates_admin(self):
        from django.contrib.auth.models import User
        self.assertIn("created", self.run_command(DJANGO_ADMIN_USERNAME="chef", DJANGO_ADMIN_PASSWORD="first-pass-1"))
        self.assertIn("updated", self.run_command(DJANGO_ADMIN_USERNAME="chef", DJANGO_ADMIN_PASSWORD="second-pass-2"))
        user = User.objects.get(username="chef")
        self.assertTrue(user.is_superuser and user.is_staff)
        self.assertTrue(user.check_password("second-pass-2"))

    def test_skips_without_env(self):
        from django.contrib.auth.models import User
        self.assertIn("skipping", self.run_command(DJANGO_ADMIN_USERNAME="", DJANGO_ADMIN_PASSWORD=""))
        self.assertFalse(User.objects.exists())
