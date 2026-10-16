import re

from django import forms
from django.conf import settings

from .models import ContactMessage, Order, Review
from .spam import SpamProtectedForm


class CheckoutForm(SpamProtectedForm, forms.ModelForm):

    class Meta:
        model = Order
        fields = (
            "full_name",
            "phone",
            "email",
            "city",
            "area",
            "address",
            "notes",
            "payment_method",
            "payment_reference",
        )

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if not 10 <= len(digits) <= 13:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone

    def clean_full_name(self):
        return self.cleaned_data["full_name"].strip()

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("payment_method")
        reference = (cleaned.get("payment_reference") or "").strip()

        if method in Order.ONLINE_PAYMENTS and method not in settings.PAYMENT_ACCOUNTS:
            self.add_error("payment_method", "This payment method isn't available right now.")
        elif method in Order.ONLINE_PAYMENTS:
            if len(reference) < 4:
                self.add_error(
                    "payment_reference",
                    "Enter the transaction ID from your payment receipt.",
                )
        else:
            reference = ""

        cleaned["payment_reference"] = reference
        return cleaned


class TrackOrderForm(forms.Form):

    order_number = forms.CharField(max_length=12)
    phone = forms.CharField(max_length=20)

    def clean_order_number(self):
        return self.cleaned_data["order_number"].strip().upper().lstrip("#")


class ReviewForm(SpamProtectedForm, forms.ModelForm):

    class Meta:
        model = Review
        fields = ("name", "rating", "title", "comment", "product")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].required = False
        self.fields["product"].queryset = (
            self.fields["product"].queryset.filter(is_available=True)
        )
        self.fields["product"].empty_label = "General experience"


class ContactForm(SpamProtectedForm, forms.ModelForm):

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "message")
