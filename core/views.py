import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from .models import (
    SiteProfile,
    AboutImage,
    Brand,
    WorkCategory,
    WorkItem,
    SocialHandle,
    RateItem,
    RateAddon,
    ContactSubmission,
)


def _humanize_count(n):
    """700000 -> '700K', 1250000 -> '1.3M', 950 -> '950'."""
    n = int(n or 0)
    if n >= 1_000_000:
        val = n / 1_000_000
        return f"{val:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 1_000:
        val = n / 1_000
        return f"{val:.1f}".rstrip("0").rstrip(".") + "K"
    return str(n)


def _stat_from_count(label, count):
    """
    Builds a dict shaped like the old Stat model (label/value/suffix/is_decimal)
    but driven by real SocialHandle.followers_count instead of a manually
    typed-in record, so the hero chips/counters can never drift out of sync
    with what's actually entered on the Social handles page.
    """
    count = int(count or 0)
    if count >= 1_000_000:
        value = round(count / 1_000_000, 1)
        suffix = "M+"
    elif count >= 1_000:
        value = round(count / 1_000)
        suffix = "K+"
    else:
        value = count
        suffix = "+"
    if isinstance(value, float) and value == int(value):
        value = int(value)
    return {
        "label": label,
        "value": value,
        "suffix": suffix,
        "is_decimal": isinstance(value, float),
        "order": 0,
    }


@method_decorator(never_cache, name="dispatch")
class AdminLoginView(LoginView):
    template_name = "core/admin_login.html"

    def get_success_url(self):
        return reverse_lazy("admin:index")


@never_cache
def index(request):
    profile = SiteProfile.objects.first()
    about_images = AboutImage.objects.only("image", "alt_text", "order")
    brands = Brand.objects.only("name", "category", "url", "rotation", "logo").all()[:15]
    categories = (
        WorkCategory.objects.prefetch_related("items").only("name", "slug", "order").all()[:4]
    )
    socials = SocialHandle.objects.filter(show_in_nav=True).only(
        "platform", "display_name", "username", "url", "followers"
    )
    all_socials = SocialHandle.objects.only(
        "platform", "display_name", "username", "url", "followers", "followers_count"
    )
    rate_items = RateItem.objects.only("deliverable", "platform", "starting_price", "order")
    rate_addons = RateAddon.objects.only("title", "description", "order")

    collab_choices = list(rate_items.values_list("deliverable", flat=True))

    engagement = SocialHandle.aggregate_engagement()
    total_reach_display = _humanize_count(engagement["total_followers"]) + "+"

    # Hero/about/rates "stats" chips, derived live from real follower counts
    # instead of a manually-typed Stat record that can drift out of sync.
    platform_stats = (
        SocialHandle.objects.filter(followers_count__gt=0)
        .order_by("-followers_count")
        .only("platform", "followers_count")
    )
    stats = [_stat_from_count(s.get_platform_display(), s.followers_count) for s in platform_stats]

    context = {
        "profile": profile,
        "stats": stats,
        "about_images": about_images,
        "brands": brands,
        "categories": categories,
        "socials": socials,
        "all_socials": all_socials,
        "rate_items": rate_items,
        "rate_addons": rate_addons,
        "collab_choices": collab_choices,
        "engagement": engagement,
        "total_reach_display": total_reach_display,
    }
    return render(request, "core/index.html", context)


@require_POST
def contact_submit(request):
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    if not all([name, email, message]):
        return JsonResponse(
            {"ok": False, "error": "Please fill in all required fields."}, status=400
        )

    ContactSubmission.objects.create(
        name=name,
        brand=data.get("brand", ""),
        email=email,
        collab_type=data.get("type", ""),
        budget=data.get("budget", ""),
        message=message,
    )
    return JsonResponse({"ok": True})
