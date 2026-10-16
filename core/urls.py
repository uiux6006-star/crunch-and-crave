from django.urls import path
from . import views


urlpatterns = [

    # ==========================================================
    # PAGES
    # ==========================================================

    path("", views.home, name="home"),
    path("menu/", views.menu, name="menu"),
    path("offers/", views.offers, name="offers"),
    path("about/", views.about, name="about"),
    path("gallery/", views.gallery, name="gallery"),
    path("reviews/", views.reviews, name="reviews"),
    path("contact/", views.contact, name="contact"),


    # ==========================================================
    # PRODUCT DETAIL
    # ==========================================================

    path("product/", views.product_detail, name="product_detail_legacy"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),


    # ==========================================================
    # CART
    # ==========================================================

    path("cart/", views.cart, name="cart"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/", views.update_cart, name="update_cart"),
    path("cart/remove/<slug:product_slug>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/clear/", views.clear_cart, name="clear_cart"),
    path("cart/promo/", views.apply_promo, name="apply_promo"),


    # ==========================================================
    # CHECKOUT & ORDERS
    # ==========================================================

    path("checkout/", views.checkout, name="checkout"),
    path("order/<str:order_number>/", views.order_success, name="order_success"),
    path("track/", views.track_order, name="track_order"),


    # ==========================================================
    # LEGAL & ADMIN HELPERS
    # ==========================================================

    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("staff/order-feed/", views.admin_order_feed, name="admin_order_feed"),

]
