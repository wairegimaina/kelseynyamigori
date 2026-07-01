from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.text import slugify
from django.utils import timezone
from core.models import (
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


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("control:dashboard")
    return render(request, "control/login.html")


def logout_view(request):
    logout(request)
    return redirect("control:login")


@login_required
def dashboard(request):
    stats = {
        "brands_count": Brand.objects.count(),
        "categories_count": WorkCategory.objects.count(),
        "items_count": WorkItem.objects.count(),
        "contacts_new": ContactSubmission.objects.filter(read=False).count(),
    }
    return render(request, "control/dashboard.html", {"stats": stats})


@login_required
@require_POST
def work_reorder_item(request, pk):
    item = get_object_or_404(WorkItem, pk=pk)
    direction = request.POST.get("direction")

    siblings = list(WorkItem.objects.filter(category=item.category).order_by("order", "pk"))
    index = next((i for i, sib in enumerate(siblings) if sib.pk == item.pk), None)

    if index is not None:
        if direction == "up" and index > 0:
            neighbor = siblings[index - 1]
            item.order, neighbor.order = neighbor.order, item.order
            item.save(update_fields=["order"])
            neighbor.save(update_fields=["order"])
        elif direction == "down" and index < len(siblings) - 1:
            neighbor = siblings[index + 1]
            item.order, neighbor.order = neighbor.order, item.order
            item.save(update_fields=["order"])
            neighbor.save(update_fields=["order"])

    return redirect("control:work_categories")


@login_required
def profile_edit(request):
    profile, _ = SiteProfile.objects.get_or_create(pk=1)
    if request.method == "POST":
        profile.display_name = request.POST.get("display_name", "").strip()
        profile.tagline = request.POST.get("tagline", "").strip()
        profile.bio_lead = request.POST.get("bio_lead", "").strip()
        profile.bio_body = request.POST.get("bio_body", "").strip()
        profile.based_in = request.POST.get("based_in", "").strip()
        profile.content_types = request.POST.get("content_types", "").strip()
        profile.contact_email = request.POST.get("contact_email", "").strip()
        profile.contact_phone = request.POST.get("contact_phone", "").strip()
        profile.portrait_caption = request.POST.get("portrait_caption", "").strip()
        profile.footer_copy = request.POST.get("footer_copy", "").strip()
        if "hero_image" in request.FILES:
            profile.hero_image = request.FILES["hero_image"]
        profile.save()
        messages.success(request, "Profile saved.")
        return redirect("control:profile_edit")
    return render(request, "control/profile.html", {"profile": profile})


@login_required
def images_list(request):
    images = AboutImage.objects.all()
    if request.method == "POST":
        AboutImage.objects.create(
            image=request.FILES.get("image"),
            alt_text=request.POST.get("alt_text", ""),
        )
        return redirect("control:images_list")
    return render(request, "control/images.html", {"images": images})


@login_required
def brands_list(request):
    brands = Brand.objects.all()
    if request.method == "POST":
        Brand.objects.create(
            name=request.POST.get("name", ""),
            category=request.POST.get("category", ""),
            logo=request.FILES.get("logo"),
            url=request.POST.get("url", ""),
            rotation=float(request.POST.get("rotation", 0)),
            order=int(request.POST.get("order", 0)),
        )
        return redirect("control:brands_list")
    return render(request, "control/brands.html", {"brands": brands})


# ── Work ─────────────────────────────────────────────────────


@login_required
def work_categories(request):
    # order_by mirrors the Meta ordering on WorkCategory ("order")
    # but explicit here so the queryset intent is visible.
    categories = WorkCategory.objects.prefetch_related("items").order_by("order", "pk")
    return render(request, "control/work.html", {"categories": categories})


@login_required
def work_add_category(request):
    if request.method == "POST":
        if WorkCategory.objects.count() >= 4:
            messages.error(request, "Maximum 4 categories allowed.")
            return redirect("control:work_categories")
        name = request.POST.get("name", "").strip()
        slug = request.POST.get("slug", "").strip() or slugify(name)
        if not name:
            messages.error(request, "Category name is required.")
            return redirect("control:work_categories")
        if WorkCategory.objects.filter(slug=slug).exists():
            messages.error(request, f'Slug "{slug}" is already in use.')
            return redirect("control:work_categories")
        # Assign next sequential order so new categories land at the end.
        next_order = WorkCategory.objects.count()
        WorkCategory.objects.create(name=name, slug=slug, order=next_order)
        messages.success(request, f'Category "{name}" added.')
    return redirect("control:work_categories")


@login_required
def work_edit_category(request, pk):
    if request.method == "POST":
        cat = get_object_or_404(WorkCategory, pk=pk)
        name = request.POST.get("name", "").strip()
        slug = request.POST.get("slug", "").strip() or slugify(name)
        if not name:
            messages.error(request, "Category name is required.")
            return redirect("control:work_categories")
        if WorkCategory.objects.filter(slug=slug).exclude(pk=pk).exists():
            messages.error(request, f'Slug "{slug}" is already in use.')
            return redirect("control:work_categories")
        cat.name = name
        cat.slug = slug
        # Allow the editor to set the display order (0 = first on frontend).
        try:
            cat.order = int(request.POST.get("order", cat.order))
        except (ValueError, TypeError):
            pass  # keep existing order if the value is invalid
        cat.save()
        messages.success(request, f'Category updated to "{name}".')
    return redirect("control:work_categories")


@login_required
def work_delete_category(request, pk):
    if request.method == "POST":
        cat = get_object_or_404(WorkCategory, pk=pk)
        name = cat.name
        cat.delete()
        messages.success(request, f'Category "{name}" and its videos deleted.')
    return redirect("control:work_categories")


@login_required
def work_add_item(request, cat_pk):
    if request.method == "POST":
        cat = get_object_or_404(WorkCategory, pk=cat_pk)
        if cat.items.count() >= 3:
            messages.error(request, f'"{cat.name}" already has 3 videos (maximum).')
            return redirect("control:work_categories")
        title = request.POST.get("title", "").strip()
        if not title:
            messages.error(request, "Video title is required.")
            return redirect("control:work_categories")
        source = request.POST.get("video_source", "upload")
        item = WorkItem(
            category=cat,
            title=title,
            client=request.POST.get("client", "").strip(),
            meta_label=request.POST.get("meta_label", "").strip(),
            post_url=request.POST.get("post_url", "").strip(),
            engagement=request.POST.get("engagement", "").strip(),
            post_views=int(request.POST.get("post_views") or 0),
            post_likes=int(request.POST.get("post_likes") or 0),
            post_comments=int(request.POST.get("post_comments") or 0),
            order=cat.items.count(),
        )
        raw_date = request.POST.get("post_date", "").strip()
        if raw_date:
            from datetime import date as _date
            try:
                item.post_date = _date.fromisoformat(raw_date)
            except ValueError:
                pass
        if source == "upload" and request.FILES.get("video_file"):
            item.video_file = request.FILES["video_file"]
        elif source == "embed":
            item.video_embed_url = request.POST.get("video_embed_url", "").strip()
        if request.FILES.get("thumbnail"):
            item.thumbnail = request.FILES["thumbnail"]
        item.save()
        messages.success(request, f'"{title}" added to {cat.name}.')
    return redirect("control:work_categories")


@login_required
def work_edit_item(request, pk):
    if request.method == "POST":
        item = get_object_or_404(WorkItem, pk=pk)
        item.title = request.POST.get("title", "").strip()
        item.client = request.POST.get("client", "").strip()
        item.meta_label = request.POST.get("meta_label", "").strip()
        item.post_url = request.POST.get("post_url", "").strip()
        item.engagement = request.POST.get("engagement", "").strip()
        item.post_views = int(request.POST.get("post_views") or 0)
        item.post_likes = int(request.POST.get("post_likes") or 0)
        item.post_comments = int(request.POST.get("post_comments") or 0)
        raw_date = request.POST.get("post_date", "").strip()
        if raw_date:
            from datetime import date as _date
            try:
                item.post_date = _date.fromisoformat(raw_date)
            except ValueError:
                pass
        source = request.POST.get("video_source", "upload")
        if source == "upload":
            if request.FILES.get("video_file"):
                # New file uploaded — replace whatever was there
                item.video_file = request.FILES["video_file"]
                item.video_embed_url = ""
            else:
                # No new file — clear any embed URL so source stays consistent
                item.video_embed_url = ""
        else:  # embed
            embed_url = request.POST.get("video_embed_url", "").strip()
            item.video_embed_url = embed_url
            # Clear uploaded file when switching to embed
            if item.video_file:
                item.video_file.delete(save=False)
                item.video_file = None
        if request.FILES.get("thumbnail"):
            item.thumbnail = request.FILES["thumbnail"]
        item.save()
        messages.success(request, f'"{item.title}" updated.')
    return redirect("control:work_categories")


@login_required
def work_delete_item(request, pk):
    if request.method == "POST":
        item = get_object_or_404(WorkItem, pk=pk)
        title = item.title
        item.delete()
        messages.success(request, f'"{title}" deleted.')
    return redirect("control:work_categories")


@login_required
@require_POST
def work_clear_item_video(request, pk):
    """
    Remove only the video file or embed URL from a WorkItem without deleting
    the item itself. The title, client, thumbnail and all other metadata are
    kept intact. The item slot remains open so a new video can be attached
    later via the normal edit form.
    """
    item = get_object_or_404(WorkItem, pk=pk)
    if item.video_file:
        item.video_file.delete(save=False)  # delete from Cloudinary
        item.video_file = None
    item.video_embed_url = ""
    item.save(update_fields=["video_file", "video_embed_url"])
    messages.success(
        request, f'Video removed from "{item.title}". The item is kept — add a new video via Edit.'
    )
    return redirect("control:work_categories")


@login_required
@require_POST
def work_fetch_stats(request):
    """
    AJAX endpoint — given a post_url, fetch live stats from the platform
    and (optionally) save them to a WorkItem if item_pk is supplied.
    Returns JSON with views, likes, comments, date, title, engagement_text.
    """
    from core.stat_fetcher import fetch_post_stats

    url = request.POST.get("post_url", "").strip()
    item_pk = request.POST.get("item_pk", "").strip()

    if not url:
        return JsonResponse({"error": "No URL provided."}, status=400)

    stats = fetch_post_stats(url)

    # Persist to WorkItem if pk given
    if item_pk:
        try:
            item = WorkItem.objects.get(pk=item_pk)
            item.post_url = url
            item.post_views = stats.get("views") or 0
            item.post_likes = stats.get("likes") or 0
            item.post_comments = stats.get("comments") or 0
            item.stats_fetched_at = timezone.now()
            if stats.get("date"):
                from datetime import date as _date
                try:
                    item.post_date = _date.fromisoformat(stats["date"])
                except ValueError:
                    pass
            if stats.get("engagement_text"):
                item.engagement = stats["engagement_text"]
            item.save(update_fields=[
                "post_url", "post_views", "post_likes", "post_comments",
                "post_date", "stats_fetched_at", "engagement",
            ])
        except WorkItem.DoesNotExist:
            pass

    return JsonResponse(stats)



    item = get_object_or_404(WorkItem, pk=pk)
    direction = request.POST.get("direction")
    siblings = list(item.category.items.order_by("order", "pk"))
    idx = next((i for i, s in enumerate(siblings) if s.pk == item.pk), None)
    if idx is None:
        return redirect("control:work_categories")
    if direction == "up" and idx > 0:
        swap = siblings[idx - 1]
    elif direction == "down" and idx < len(siblings) - 1:
        swap = siblings[idx + 1]
    else:
        return redirect("control:work_categories")
    item.order, swap.order = swap.order, item.order
    if item.order == swap.order:
        item.order = idx - 1 if direction == "up" else idx + 1
        swap.order = idx if direction == "up" else idx
    item.save(update_fields=["order"])
    swap.save(update_fields=["order"])
    return redirect("control:work_categories")


# ── Social ───────────────────────────────────────────────────


@login_required
def social_handles(request):
    socials = SocialHandle.objects.all()
    if request.method == "POST":

        def _to_int(field):
            raw = request.POST.get(field, "").replace(",", "").strip()
            try:
                return int(raw) if raw else 0
            except ValueError:
                return 0

        SocialHandle.objects.create(
            platform=request.POST.get("platform", ""),
            display_name=request.POST.get("display_name", ""),
            username=request.POST.get("username", ""),
            url=request.POST.get("url", ""),
            followers=request.POST.get("followers", ""),
            followers_count=_to_int("followers_count"),
            total_likes=_to_int("total_likes"),
            total_views=_to_int("total_views"),
            total_comments=_to_int("total_comments"),
            total_shares=_to_int("total_shares"),
        )
        return redirect("control:social_handles")
    engagement = SocialHandle.aggregate_engagement()
    return render(
        request,
        "control/social.html",
        {"socials": socials, "engagement": engagement},
    )


@login_required
def social_edit(request, pk):
    if request.method == "POST":
        s = get_object_or_404(SocialHandle, pk=pk)

        def _to_int(field, default=0):
            raw = request.POST.get(field, "").replace(",", "").strip()
            try:
                return int(raw) if raw else default
            except ValueError:
                return default

        s.platform = request.POST.get("platform", s.platform)
        s.display_name = request.POST.get("display_name", "").strip()
        s.username = request.POST.get("username", "").strip()
        s.url = request.POST.get("url", "").strip()
        s.followers = request.POST.get("followers", "").strip()
        s.followers_count = _to_int("followers_count", s.followers_count)
        s.total_likes = _to_int("total_likes", s.total_likes)
        s.total_views = _to_int("total_views", s.total_views)
        s.total_comments = _to_int("total_comments", s.total_comments)
        s.total_shares = _to_int("total_shares", s.total_shares)
        s.show_in_nav = bool(request.POST.get("show_in_nav"))
        s.save()
        messages.success(request, f'"{s.username}" updated.')
    return redirect("control:social_handles")


@login_required
def social_delete(request, pk):
    if request.method == "POST":
        s = get_object_or_404(SocialHandle, pk=pk)
        username = s.username
        s.delete()
        messages.success(request, f'"{username}" deleted.')
    return redirect("control:social_handles")


# ── Rates ────────────────────────────────────────────────────


@login_required
def rates_list(request):
    rate_items = RateItem.objects.all()
    rate_addons = RateAddon.objects.all()
    return render(
        request,
        "control/rates.html",
        {
            "rate_items": rate_items,
            "rate_addons": rate_addons,
        },
    )


@login_required
def rate_item_add(request):
    if request.method == "POST":
        deliverable = request.POST.get("deliverable", "").strip()
        starting_price = request.POST.get("starting_price", "").strip()
        if not deliverable or not starting_price:
            messages.error(request, "Deliverable and starting price are required.")
            return redirect("control:rates_list")
        RateItem.objects.create(
            deliverable=deliverable,
            platform=request.POST.get("platform", "").strip(),
            starting_price=starting_price,
        )
        messages.success(request, f'Rate item "{deliverable}" added.')
    return redirect("control:rates_list")


@login_required
def rate_item_edit(request, pk):
    if request.method == "POST":
        item = get_object_or_404(RateItem, pk=pk)
        deliverable = request.POST.get("deliverable", "").strip()
        starting_price = request.POST.get("starting_price", "").strip()
        if not deliverable or not starting_price:
            messages.error(request, "Deliverable and starting price are required.")
            return redirect("control:rates_list")
        item.deliverable = deliverable
        item.platform = request.POST.get("platform", "").strip()
        item.starting_price = starting_price
        item.save()
        messages.success(request, f'Rate item "{item.deliverable}" updated.')
    return redirect("control:rates_list")


@login_required
def rate_item_delete(request, pk):
    if request.method == "POST":
        item = get_object_or_404(RateItem, pk=pk)
        deliverable = item.deliverable
        item.delete()
        messages.success(request, f'Rate item "{deliverable}" deleted.')
    return redirect("control:rates_list")


@login_required
def rate_addon_add(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        if not title or not description:
            messages.error(request, "Title and description are required.")
            return redirect("control:rates_list")
        RateAddon.objects.create(title=title, description=description)
        messages.success(request, f'Add-on "{title}" added.')
    return redirect("control:rates_list")


@login_required
def rate_addon_edit(request, pk):
    if request.method == "POST":
        addon = get_object_or_404(RateAddon, pk=pk)
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        if not title or not description:
            messages.error(request, "Title and description are required.")
            return redirect("control:rates_list")
        addon.title = title
        addon.description = description
        addon.save()
        messages.success(request, f'Add-on "{addon.title}" updated.')
    return redirect("control:rates_list")


@login_required
def rate_addon_delete(request, pk):
    if request.method == "POST":
        addon = get_object_or_404(RateAddon, pk=pk)
        title = addon.title
        addon.delete()
        messages.success(request, f'Add-on "{title}" deleted.')
    return redirect("control:rates_list")


# ── Contacts ─────────────────────────────────────────────────


@login_required
def contacts_list(request):
    qs = ContactSubmission.objects.all()
    status_filter = request.GET.get("status", "")
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, "control/contacts.html", {"contacts": qs})


@login_required
def contact_add(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        if not name or not email:
            messages.error(request, "Name and email are required.")
            return redirect("control:contacts_list")
        ContactSubmission.objects.create(
            name=name,
            email=email,
            brand=request.POST.get("brand", "").strip(),
            collab_type=request.POST.get("collab_type", "").strip(),
            budget=request.POST.get("budget", "").strip(),
            message=request.POST.get("message", "").strip(),
            status=request.POST.get("status", "new"),
            read=False,
        )
        messages.success(request, f'Contact "{name}" added.')
    return redirect("control:contacts_list")


@login_required
def contact_edit(request, pk):
    if request.method == "POST":
        contact = get_object_or_404(ContactSubmission, pk=pk)
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        if not name or not email:
            messages.error(request, "Name and email are required.")
            return redirect("control:contacts_list")
        contact.name = name
        contact.email = email
        contact.brand = request.POST.get("brand", "").strip()
        contact.collab_type = request.POST.get("collab_type", "").strip()
        contact.budget = request.POST.get("budget", "").strip()
        contact.message = request.POST.get("message", "").strip()
        contact.status = request.POST.get("status", contact.status)
        contact.read = bool(request.POST.get("read"))
        contact.save()
        messages.success(request, f'"{contact.name}" updated.')
    return redirect("control:contacts_list")


@login_required
def contact_delete(request, pk):
    if request.method == "POST":
        contact = get_object_or_404(ContactSubmission, pk=pk)
        name = contact.name
        contact.delete()
        messages.success(request, f'"{name}" deleted.')
    return redirect("control:contacts_list")


# ── Brand edit / delete ───────────────────────────────────────


@login_required
def brand_edit(request, pk):
    if request.method == "POST":
        brand = get_object_or_404(Brand, pk=pk)
        brand.name = request.POST.get("name", "").strip()
        brand.category = request.POST.get("category", "").strip()
        brand.url = request.POST.get("url", "").strip()
        try:
            brand.rotation = float(request.POST.get("rotation", 0))
        except ValueError:
            brand.rotation = 0
        try:
            brand.order = int(request.POST.get("order", brand.order))
        except ValueError:
            pass
        if request.FILES.get("logo"):
            brand.logo = request.FILES["logo"]
        brand.save()
        messages.success(request, f'Brand "{brand.name}" updated.')
    return redirect("control:brands_list")


@login_required
def brand_delete(request, pk):
    if request.method == "POST":
        brand = get_object_or_404(Brand, pk=pk)
        name = brand.name
        brand.delete()
        messages.success(request, f'Brand "{name}" deleted.')
    return redirect("control:brands_list")


# ── Image edit / delete ───────────────────────────────────────


@login_required
def image_edit(request, pk):
    if request.method == "POST":
        img = get_object_or_404(AboutImage, pk=pk)
        img.alt_text = request.POST.get("alt_text", "").strip()
        img.save()
        messages.success(request, "Image caption updated.")
    return redirect("control:images_list")


@login_required
def image_delete(request, pk):
    if request.method == "POST":
        img = get_object_or_404(AboutImage, pk=pk)
        img.delete()
        messages.success(request, "Image deleted.")
    return redirect("control:images_list")


# ── Campaigns ─────────────────────────────────────────────────

from django.http import HttpResponse
from core.models import Campaign, CampaignDeliverable, CampaignPost, CampaignChecklist
from datetime import date


@login_required
def campaigns_list(request):
    campaigns = Campaign.objects.select_related("brand").prefetch_related(
        "deliverables", "posts", "checklist"
    )
    stats = {
        "total": campaigns.count(),
        "active": campaigns.filter(status="active").count(),
        "completed": campaigns.filter(status="completed").count(),
        "pending_deliverables": sum(
            max(c.total_required - c.total_completed, 0) for c in campaigns
        ),
        "total_posts": sum(c.posts.count() for c in campaigns),
    }
    brands = Brand.objects.all()
    return render(request, "control/campaigns.html", {
        "campaigns": campaigns,
        "stats": stats,
        "brands": brands,
        "platform_choices": [("instagram","Instagram"),("tiktok","TikTok"),("facebook","Facebook"),("youtube","YouTube"),("twitter","X / Twitter"),("snapchat","Snapchat"),("threads","Threads")],
        "content_type_choices": [("video","Video"),("reel","Reel"),("story","Story"),("post","Post"),("live","Live"),("short","Short")],
        "status_choices": [("draft","Draft"),("active","Active"),("completed","Completed"),("cancelled","Cancelled")],
        "payment_status_choices": [("unpaid","Unpaid"),("partial","Partial"),("paid","Paid")],
        "currency_choices": [("KES","KES"),("USD","USD"),("EUR","EUR"),("GBP","GBP")],
        "today": date.today().isoformat(),
    })


@login_required
def campaign_add(request):
    if request.method == "POST":
        brand_id = request.POST.get("brand")
        brand = Brand.objects.filter(pk=brand_id).first()
        campaign = Campaign.objects.create(
            brand=brand,
            campaign_name=request.POST.get("campaign_name", "").strip(),
            status=request.POST.get("status", "draft"),
            start_date=request.POST.get("start_date") or None,
            end_date=request.POST.get("end_date") or None,
            payment_amount=request.POST.get("payment_amount") or 0,
            currency=request.POST.get("currency", "KES"),
            payment_status=request.POST.get("payment_status", "unpaid"),
            deposit_amount=request.POST.get("deposit_amount") or 0,
            notes=request.POST.get("notes", "").strip(),
        )
        # Deliverables — sent as parallel arrays
        platforms = request.POST.getlist("del_platform")
        ctypes = request.POST.getlist("del_content_type")
        quantities = request.POST.getlist("del_quantity")
        for p, ct, q in zip(platforms, ctypes, quantities):
            if p and ct and q:
                CampaignDeliverable.objects.create(
                    campaign=campaign, platform=p, content_type=ct,
                    required_quantity=int(q) if q.isdigit() else 1
                )
        # Checklist items
        checklist_items = request.POST.getlist("checklist_item")
        for i, item in enumerate(checklist_items):
            if item.strip():
                CampaignChecklist.objects.create(campaign=campaign, item=item.strip(), order=i)
        messages.success(request, f'Campaign "{campaign.campaign_name}" created.')
    return redirect("control:campaigns_list")


@login_required
def campaign_edit(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == "POST":
        brand_id = request.POST.get("brand")
        campaign.brand = Brand.objects.filter(pk=brand_id).first()
        campaign.campaign_name = request.POST.get("campaign_name", "").strip()
        campaign.status = request.POST.get("status", campaign.status)
        campaign.start_date = request.POST.get("start_date") or None
        campaign.end_date = request.POST.get("end_date") or None
        campaign.payment_amount = request.POST.get("payment_amount") or 0
        campaign.currency = request.POST.get("currency", campaign.currency)
        campaign.payment_status = request.POST.get("payment_status", campaign.payment_status)
        campaign.deposit_amount = request.POST.get("deposit_amount") or 0
        campaign.notes = request.POST.get("notes", "").strip()
        campaign.save()
        messages.success(request, f'Campaign "{campaign.campaign_name}" updated.')
    return redirect("control:campaigns_list")


@login_required
def campaign_delete(request, pk):
    if request.method == "POST":
        campaign = get_object_or_404(Campaign, pk=pk)
        name = campaign.campaign_name
        campaign.delete()
        messages.success(request, f'Campaign "{name}" deleted.')
    return redirect("control:campaigns_list")


@login_required
def campaign_post_add(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == "POST":
        deliverable_id = request.POST.get("deliverable") or None
        deliverable = (
            CampaignDeliverable.objects.filter(pk=deliverable_id).first()
            if deliverable_id else None
        )
        CampaignPost.objects.create(
            campaign=campaign,
            deliverable=deliverable,
            platform=request.POST.get("platform", ""),
            content_type=request.POST.get("content_type", ""),
            post_url=request.POST.get("post_url", "").strip(),
            caption=request.POST.get("caption", "").strip(),
            posting_date=request.POST.get("posting_date") or None,
            views=int(request.POST.get("views") or 0),
            likes=int(request.POST.get("likes") or 0),
            comments=int(request.POST.get("comments") or 0),
            notes=request.POST.get("notes", "").strip(),
        )
        messages.success(request, "Post added.")
    return redirect("control:campaigns_list")


@login_required
def campaign_post_edit(request, pk):
    if request.method == "POST":
        post = get_object_or_404(CampaignPost, pk=pk)
        post.platform = request.POST.get("platform", post.platform)
        post.content_type = request.POST.get("content_type", post.content_type)
        post.post_url = request.POST.get("post_url", "").strip()
        post.caption = request.POST.get("caption", "").strip()
        post.notes = request.POST.get("notes", "").strip()
        post.posting_date = request.POST.get("posting_date") or None
        post.views = int(request.POST.get("views") or 0)
        post.likes = int(request.POST.get("likes") or 0)
        post.comments = int(request.POST.get("comments") or 0)
        deliverable_id = request.POST.get("deliverable") or None
        post.deliverable = (
            CampaignDeliverable.objects.filter(pk=deliverable_id).first()
            if deliverable_id else None
        )
        post.save()
        messages.success(request, "Post updated.")
    return redirect("control:campaigns_list")


@login_required
def campaign_post_delete(request, pk):
    if request.method == "POST":
        post = get_object_or_404(CampaignPost, pk=pk)
        post.delete()
        messages.success(request, "Post removed.")
    return redirect("control:campaigns_list")


@login_required
def campaign_checklist_toggle(request, pk):
    if request.method == "POST":
        item = get_object_or_404(CampaignChecklist, pk=pk)
        item.is_done = not item.is_done
        item.save(update_fields=["is_done"])
    return redirect("control:campaigns_list")


@login_required
def campaign_deliverable_delete(request, pk):
    if request.method == "POST":
        d = get_object_or_404(CampaignDeliverable, pk=pk)
        d.delete()
        messages.success(request, "Deliverable removed.")
    return redirect("control:campaigns_list")


@login_required
@require_POST
def campaign_fetch_stats(request):
    """
    AJAX endpoint — given a post URL, fetch live stats and return JSON.
    Used by the 'Fetch Stats' button inside the Log-a-Post form on the
    Campaigns page.  Does NOT persist anything; the form submit does that.
    """
    from core.stat_fetcher import fetch_post_stats

    url = request.POST.get("post_url", "").strip()
    if not url:
        return JsonResponse({"error": "No URL provided."}, status=400)

    stats = fetch_post_stats(url)
    return JsonResponse(stats)


@login_required
def campaign_report_download(request, pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    import io, urllib.request, tempfile, os

    campaign = get_object_or_404(
        Campaign.objects.select_related("brand").prefetch_related("deliverables", "posts", "checklist"),
        pk=pk
    )
    brand_name = campaign.brand.name if campaign.brand else "No Brand"
    safe_name = "".join(c for c in f"{brand_name}_{campaign.campaign_name}" if c.isalnum() or c in "_- ")

    # Profile name for header
    from core.models import SiteProfile
    _profile = SiteProfile.objects.filter(pk=1).first()
    creator_name = _profile.display_name if _profile else "Mary Ann"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title=f"{brand_name} — {campaign.campaign_name}",
    )

    W = A4[0] - 36*mm  # usable width

    # ── Colour palette ──
    C_BLACK   = colors.HexColor("#111111")
    C_WHITE   = colors.HexColor("#ffffff")
    C_ACCENT  = colors.HexColor("#1a1a2e")   # deep navy header
    C_LIGHT   = colors.HexColor("#f5f5f7")   # light grey rows
    C_MID     = colors.HexColor("#e0e0e8")
    C_GREEN   = colors.HexColor("#2e7d32")
    C_BLUE    = colors.HexColor("#1565c0")
    C_ORANGE  = colors.HexColor("#e65100")
    C_RED     = colors.HexColor("#c62828")

    STATUS_COLOURS = {
        "active": C_GREEN, "completed": C_BLUE,
        "draft": colors.HexColor("#555"), "cancelled": C_RED,
    }
    PAY_COLOURS = {
        "paid": C_GREEN, "partial": C_ORANGE, "unpaid": C_RED,
    }

    styles = getSampleStyleSheet()

    def sty(name, **kw):
        base = styles.get(name, styles["Normal"])
        return ParagraphStyle(f"custom_{id(kw)}", parent=base, **kw)

    H1 = sty("Normal", fontSize=22, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=2)
    H2 = sty("Normal", fontSize=11, fontName="Helvetica-Bold", textColor=C_ACCENT, spaceBefore=10, spaceAfter=4)
    LABEL = sty("Normal", fontSize=8, fontName="Helvetica", textColor=colors.HexColor("#666666"))
    VALUE = sty("Normal", fontSize=10, fontName="Helvetica-Bold", textColor=C_BLACK)
    SMALL = sty("Normal", fontSize=8, fontName="Helvetica", textColor=colors.HexColor("#444444"))
    URL_S = sty("Normal", fontSize=7, fontName="Helvetica", textColor=C_BLUE, wordWrap="LTR", leading=9)
    CAP_S = sty("Normal", fontSize=8, fontName="Helvetica", textColor=colors.HexColor("#333"), leading=10)
    TINY  = sty("Normal", fontSize=7.5, fontName="Helvetica", textColor=colors.HexColor("#444444"))
    NUM_S = sty("Normal", fontSize=8.5, fontName="Helvetica-Bold", textColor=C_BLACK, alignment=TA_CENTER)

    story = []

    # ── Header banner: brand logo | brand+campaign name | creator ──
    _logo_tmp = None
    logo_cell = Paragraph("", sty("Normal"))
    if campaign.brand and campaign.brand.logo:
        try:
            _logo_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            urllib.request.urlretrieve(campaign.brand.logo.url, _logo_tmp.name)
            _li = RLImage(_logo_tmp.name, width=30*mm, height=13*mm)
            _li.hAlign = "LEFT"
            logo_cell = _li
        except Exception:
            logo_cell = Paragraph(brand_name, sty("Normal", fontSize=12, fontName="Helvetica-Bold", textColor=C_WHITE))

    header_data = [[
        logo_cell,
        Paragraph(
            f"<b>{brand_name}</b><br/>"
            f"<font size=9 color=#bbbbbb>{campaign.campaign_name}</font>",
            sty("Normal", fontSize=14, fontName="Helvetica-Bold", textColor=C_WHITE,
                alignment=TA_CENTER, leading=20),
        ),
        Paragraph(
            f"<font size=7.5 color=#aaaaaa>Creator</font><br/><b>{creator_name}</b>",
            sty("Normal", fontSize=12, fontName="Helvetica-Bold", textColor=C_WHITE,
                alignment=TA_RIGHT, leading=17),
        ),
    ]]
    header_table = Table(header_data, colWidths=[W*0.22, W*0.50, W*0.28])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_ACCENT),
        ("TOPPADDING",    (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # Campaign name + status pill side by side
    status_col = PAY_COLOURS.get(campaign.payment_status, C_BLACK)
    stat_col   = STATUS_COLOURS.get(campaign.status, C_BLACK)
    camp_row = [[
        Paragraph(campaign.campaign_name, sty("Normal", fontSize=16, fontName="Helvetica-Bold", textColor=C_BLACK)),
        Paragraph(campaign.get_status_display().upper(),
                  sty("Normal", fontSize=8, fontName="Helvetica-Bold", textColor=C_WHITE, alignment=TA_CENTER)),
    ]]
    camp_t = Table(camp_row, colWidths=[W*0.75, W*0.25])
    camp_t.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
        ("BACKGROUND",   (1,0),(1,0), stat_col),
        ("TEXTCOLOR",    (1,0),(1,0), C_WHITE),
        ("TOPPADDING",   (1,0),(1,0), 5),
        ("BOTTOMPADDING",(1,0),(1,0), 5),
        ("ROUNDEDCORNERS",[4]),
    ]))
    story.append(camp_t)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width=W, thickness=1, color=C_MID))
    story.append(Spacer(1, 8))

    # ── Summary info grid ──
    def kv(label, value):
        return [Paragraph(label, LABEL), Paragraph(str(value), VALUE)]

    start = campaign.start_date.strftime("%d %b %Y") if campaign.start_date else "—"
    end   = campaign.end_date.strftime("%d %b %Y")   if campaign.end_date   else "—"
    progress_txt = f"{campaign.total_completed} / {campaign.total_required} posts  ({campaign.progress_percent}%)"

    info_data = [
        kv("BRAND", brand_name) + kv("CAMPAIGN STATUS", campaign.get_status_display()),
        kv("START DATE", start) + kv("END DATE", end),
        kv("DELIVERABLE PROGRESS", progress_txt) + ["", ""],
    ]
    cw = W / 4
    info_t = Table(info_data, colWidths=[cw*0.9, cw*1.1, cw*0.9, cw*1.1])
    info_t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), C_LIGHT),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[C_LIGHT, C_WHITE]),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),
        ("RIGHTPADDING", (0,0),(-1,-1), 8),
        ("GRID",         (0,0),(-1,-1), 0.5, C_MID),
        ("ROUNDEDCORNERS",[4]),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 14))

    # ── Deliverables ──
    story.append(Paragraph("DELIVERABLES", H2))
    story.append(HRFlowable(width=W, thickness=0.5, color=C_MID))
    story.append(Spacer(1, 4))

    deliverables = list(campaign.deliverables.all())
    if deliverables:
        _HDR = lambda t, center=False: Paragraph(t, sty(
            "Normal", fontSize=8, fontName="Helvetica-Bold", textColor=C_WHITE,
            alignment=TA_CENTER if center else TA_LEFT))
        del_data = [[_HDR("PLATFORM"), _HDR("CONTENT TYPE"), _HDR("AGREED", True), _HDR("DELIVERED", True)]]
        for d in deliverables:
            # Count by FK first, then fall back to platform+content_type match
            delivered = campaign.posts.filter(deliverable=d).count()
            if delivered == 0:
                delivered = campaign.posts.filter(
                    platform=d.platform, content_type=d.content_type).count()
            del_data.append([
                Paragraph(d.get_platform_display(), SMALL),
                Paragraph(d.get_content_type_display(), SMALL),
                Paragraph(str(d.required_quantity),
                          sty("Normal", fontSize=9, fontName="Helvetica-Bold",
                              textColor=C_BLACK, alignment=TA_CENTER)),
                Paragraph(str(delivered),
                          sty("Normal", fontSize=9, fontName="Helvetica-Bold",
                              textColor=C_GREEN if delivered >= d.required_quantity else C_ORANGE,
                              alignment=TA_CENTER)),
            ])
        # 4 cols: platform 35%, content 35%, agreed 15%, delivered 15%
        del_t = Table(del_data, colWidths=[W*0.35, W*0.35, W*0.15, W*0.15])
        del_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  C_ACCENT),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("RIGHTPADDING",  (0,0), (-1,-1), 8),
            ("GRID",          (0,0), (-1,-1), 0.4, C_MID),
            ("ALIGN",         (2,0), (3,-1),  "CENTER"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(del_t)
    else:
        story.append(Paragraph("No deliverables recorded.", SMALL))
    story.append(Spacer(1, 14))

    # ── Published Posts ──
    story.append(Paragraph("PUBLISHED POSTS", H2))
    story.append(HRFlowable(width=W, thickness=0.5, color=C_MID))
    story.append(Spacer(1, 4))

    posts = list(campaign.posts.all())
    if posts:
        _PHDR = lambda t, center=False: Paragraph(t, sty(
            "Normal", fontSize=7.5, fontName="Helvetica-Bold", textColor=C_WHITE,
            alignment=TA_CENTER if center else TA_LEFT))
        post_data = [[
            _PHDR("PLATFORM"), _PHDR("DATE"),
            _PHDR("VIEWS", True), _PHDR("LIKES", True), _PHDR("COMMENTS", True),
            _PHDR("POST URL"),
        ]]
        for post in posts:
            date_str = post.posting_date.strftime("%d %b %Y") if post.posting_date else "—"
            # Shorten URL to domain + path stub so it fits
            url_raw = post.post_url or ""
            if url_raw:
                try:
                    from urllib.parse import urlparse as _up
                    _p = _up(url_raw)
                    _host = _p.netloc.replace("www.", "")
                    _path = _p.path[:28] + ("…" if len(_p.path) > 28 else "")
                    url_display = _host + _path
                except Exception:
                    url_display = url_raw[:38] + ("…" if len(url_raw) > 38 else "")
            else:
                url_display = "—"
            post_data.append([
                Paragraph(post.get_platform_display(), TINY),
                Paragraph(date_str, TINY),
                Paragraph(f"{post.views:,}" if post.views else "—", NUM_S),
                Paragraph(f"{post.likes:,}"  if post.likes  else "—", NUM_S),
                Paragraph(f"{post.comments:,}" if post.comments else "—", NUM_S),
                Paragraph(
                    f'<link href="{url_raw}">{url_display}</link>' if url_raw else "—",
                    URL_S),
            ])
        # platform 14%, date 12%, views 10%, likes 10%, comments 11%, url 43%
        post_t = Table(post_data, colWidths=[W*0.14, W*0.12, W*0.10, W*0.10, W*0.17, W*0.43])
        post_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  C_ACCENT),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("RIGHTPADDING",  (0,0), (-1,-1), 6),
            ("GRID",          (0,0), (-1,-1), 0.4, C_MID),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",         (2,0), (4,-1),  "CENTER"),
        ]))
        story.append(post_t)

        # Captions + notes listed below the table (one line each)
        cap_posts = [p for p in posts if p.caption or p.notes]
        if cap_posts:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Captions & Notes", sty(
                "Normal", fontSize=8, fontName="Helvetica-Bold",
                textColor=colors.HexColor("#666"), spaceAfter=3)))
            for p in cap_posts:
                txt = p.caption or ""
                if p.notes:
                    txt += (" — " if txt else "") + p.notes
                lbl = f"{p.get_platform_display()}"
                if p.posting_date:
                    lbl += f" {p.posting_date.strftime('%d %b')}"
                story.append(Paragraph(
                    f"<b>{lbl}:</b> {txt}",
                    sty("Normal", fontSize=7.5, textColor=colors.HexColor("#444"),
                        leading=11, spaceBefore=2)))
    else:
        story.append(Paragraph("No posts recorded yet.", SMALL))
    story.append(Spacer(1, 14))

    # ── Checklist ──
    checklist = list(campaign.checklist.all())
    if checklist:
        story.append(Paragraph("BRAND REQUIREMENTS CHECKLIST", H2))
        story.append(HRFlowable(width=W, thickness=0.5, color=C_MID))
        story.append(Spacer(1, 4))
        chk_data = []
        for item in checklist:
            tick = "✓" if item.is_done else "○"
            tick_col = C_GREEN if item.is_done else C_RED
            chk_data.append([
                Paragraph(tick, sty("Normal", fontSize=11, fontName="Helvetica-Bold", textColor=tick_col, alignment=TA_CENTER)),
                Paragraph(item.item, sty("Normal", fontSize=9, textColor=C_BLACK if not item.is_done else colors.HexColor("#666"))),
            ])
        chk_t = Table(chk_data, colWidths=[W*0.08, W*0.92])
        chk_t.setStyle(TableStyle([
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[C_WHITE, C_LIGHT]),
            ("TOPPADDING",   (0,0),(-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("LEFTPADDING",  (0,0),(-1,-1), 6),
            ("RIGHTPADDING", (0,0),(-1,-1), 6),
            ("GRID",         (0,0),(-1,-1), 0.3, C_MID),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ]))
        story.append(chk_t)
        story.append(Spacer(1, 14))

    # ── Notes ──
    if campaign.notes:
        story.append(Paragraph("NOTES", H2))
        story.append(HRFlowable(width=W, thickness=0.5, color=C_MID))
        story.append(Spacer(1, 4))
        story.append(Paragraph(campaign.notes, sty("Normal", fontSize=9, textColor=C_BLACK, backColor=C_LIGHT,
                                                     leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4)))
        story.append(Spacer(1, 10))

    # ── Footer ──
    from datetime import date as _date
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width=W, thickness=0.5, color=C_MID))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Generated {_date.today().strftime('%d %B %Y')} &nbsp;·&nbsp; {creator_name} Campaign Report",
        sty("Normal", fontSize=7.5, textColor=colors.HexColor("#999"), alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)

    # Clean up temp logo file
    if _logo_tmp:
        try: os.unlink(_logo_tmp.name)
        except Exception: pass

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{safe_name}_report.pdf"'
    return response
