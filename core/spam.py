"""Invisible spam protection for public forms.

Three checks, none of which bother real customers:

1. Honeypot — a hidden field humans never see; bots fill it in.
2. Timing — a signed timestamp; forms submitted faster than a human
   could type them are rejected.
3. Rate limit — each IP may only submit a form a few times per window.
"""

import time

from django import forms
from django.conf import settings
from django.core import signing
from django.core.cache import cache


SALT = "nj-form-timestamp"
SPAM_MESSAGE = "Your submission looked automated. Please wait a moment and try again."


def make_token():
    return signing.dumps(time.time(), salt=SALT)


class SpamProtectedForm(forms.Form):
    """Mixin for forms: add these hidden fields and checks."""

    hp_contact = forms.CharField(required=False)
    form_ts = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["form_ts"].initial = make_token()

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("hp_contact"):
            raise forms.ValidationError(SPAM_MESSAGE)

        try:
            started = signing.loads(cleaned.get("form_ts") or "", salt=SALT, max_age=6 * 3600)
        except signing.BadSignature:
            raise forms.ValidationError("This form expired. Please refresh the page and try again.")

        if time.time() - started < settings.SPAM_MIN_SECONDS:
            raise forms.ValidationError(SPAM_MESSAGE)

        return cleaned


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def rate_limited(request, name):
    """True when this IP has used up its submissions for `name`.

    Call only for submissions that are about to be accepted.
    """
    limit, window = settings.RATE_LIMITS[name]
    key = f"rl:{name}:{client_ip(request)}"
    count = cache.get(key, 0)
    if count >= limit:
        return True
    if count == 0:
        cache.set(key, 1, window)
    else:
        cache.incr(key)
    return False
