from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from cloudinary_storage.storage import MediaCloudinaryStorage, VideoMediaCloudinaryStorage

PLATFORM_CHOICES = [
    ("instagram", "Instagram"),
    ("tiktok", "TikTok"),
    ("facebook", "Facebook"),
    ("youtube", "YouTube"),
    ("twitter", "X / Twitter"),
    ("snapchat", "Snapchat"),
    ("pinterest", "Pinterest"),
    ("linkedin", "LinkedIn"),
    ("threads", "Threads"),
    ("whatsapp", "WhatsApp"),
]


def validate_image_size(file):
    max_size = getattr(settings, "MAX_IMAGE_UPLOAD_SIZE", 4 * 1024 * 1024)
    if file.size > max_size:
        raise ValidationError(f"Image file size must not exceed {max_size // (1024 * 1024)}MB.")


def validate_video_size(file):
    max_size = getattr(settings, "MAX_VIDEO_UPLOAD_SIZE", 10 * 1024 * 1024)
    if file.size > max_size:
        raise ValidationError(f"Video file size must not exceed {max_size // (1024 * 1024)}MB.")


class SiteProfile(models.Model):
    display_name = models.CharField(max_length=100, default="KESLEY")
    tagline = models.CharField(max_length=200, default="Creator & Influencer / Media Kit 2026")
    bio_lead = models.CharField(
        max_length=300,
        default="I'm Kesley — content creator, lifestyle influencer, and digital storyteller.",
    )
    bio_body = models.TextField(default="", help_text="Paragraphs separated by newlines")
    based_in = models.CharField(max_length=100, default="Nairobi, Kenya")
    content_types = models.CharField(max_length=200, default="Lifestyle · Fashion · Beauty · Vlogs")
    contact_email = models.EmailField(default="hello@kesley.co.ke")
    contact_phone = models.CharField(max_length=50, blank=True)
    hero_image = models.ImageField(
        upload_to="hero/",
        blank=True,
        null=True,
        storage=MediaCloudinaryStorage(),
    )
    portrait_caption = models.CharField(max_length=200, default="", blank=True)
    footer_copy = models.CharField(max_length=200, default="© 2026 Kesley. All rights reserved.")
    about_lead_text = models.CharField(max_length=200, default="")
    about_paragraph_1 = models.TextField(default="", blank=True)
    about_paragraph_2 = models.TextField(default="", blank=True)
    about_paragraph_3 = models.TextField(default="", blank=True)

    class Meta:
        verbose_name = "Site Profile"

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if self.pk and self.hero_image:
            try:
                old = SiteProfile.objects.get(pk=self.pk)
                if old.hero_image and old.hero_image != self.hero_image:
                    old.hero_image.delete(save=False)
            except SiteProfile.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class Stat(models.Model):
    label = models.CharField(max_length=60)
    value = models.CharField(max_length=20, help_text="e.g. 700 or 8.4")
    suffix = models.CharField(max_length=20, blank=True, help_text="e.g. K+ or .4%")
    order = models.PositiveSmallIntegerField(default=0)
    is_decimal = models.BooleanField(default=False, help_text="Animate as decimal?")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.label}: {self.value}{self.suffix}"


class AboutImage(models.Model):
    image = models.ImageField(upload_to="about/", storage=MediaCloudinaryStorage())
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.alt_text or f"About image #{self.order}"

    def save(self, *args, **kwargs):
        if self.pk and self.image:
            try:
                old = AboutImage.objects.get(pk=self.pk)
                if old.image and old.image != self.image:
                    old.image.delete(save=False)
            except AboutImage.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True, help_text="e.g. Beauty & Skincare")
    logo = models.ImageField(
        upload_to="brands/", blank=True, null=True, storage=MediaCloudinaryStorage()
    )
    url = models.URLField(blank=True)
    rotation = models.FloatField(default=0, help_text="CSS tilt in degrees (-3 to 3)")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk and self.logo:
            try:
                old = Brand.objects.get(pk=self.pk)
                if old.logo and old.logo != self.logo:
                    old.logo.delete(save=False)
            except Brand.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.logo:
            self.logo.delete(save=False)
        super().delete(*args, **kwargs)


class WorkCategory(models.Model):
    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True, help_text="Filter key e.g. fashion")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Work Category"
        verbose_name_plural = "Work Categories"

    def __str__(self):
        return self.name


class WorkItem(models.Model):
    category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=200)
    client = models.CharField(max_length=100, blank=True)
    meta_label = models.CharField(max_length=100, blank=True, help_text="e.g. Fashion · TikTok")
    video_file = models.FileField(
        upload_to="work/videos/",
        blank=True,
        null=True,
        storage=VideoMediaCloudinaryStorage(),
        validators=[validate_video_size],
        help_text="Upload MP4/MOV directly (max 10MB)",
    )
    video_embed_url = models.URLField(blank=True, help_text="YouTube/TikTok embed URL")
    thumbnail = models.ImageField(
        upload_to="work/thumbs/",
        blank=True,
        null=True,
        storage=MediaCloudinaryStorage(),
        validators=[validate_image_size],
    )
    order = models.PositiveSmallIntegerField(default=0)
    post_url = models.URLField(blank=True, help_text="Link to the live TikTok/Instagram post")
    engagement = models.CharField(max_length=60, blank=True)
    post_views = models.PositiveIntegerField(default=0)
    post_likes = models.PositiveIntegerField(default=0)
    post_comments = models.PositiveIntegerField(default=0)
    post_date = models.DateField(null=True, blank=True)
    stats_fetched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["category__order", "order"]

    def __str__(self):
        return f"{self.category.name} — {self.title}"

    @property
    def embed_src(self):
        if self.video_file:
            return self.video_file.url
        return self.video_embed_url

    @property
    def is_uploaded(self):
        return bool(self.video_file)

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = WorkItem.objects.get(pk=self.pk)
                if old.video_file and old.video_file != self.video_file:
                    old.video_file.delete(save=False)
                if old.thumbnail and old.thumbnail != self.thumbnail:
                    old.thumbnail.delete(save=False)
            except WorkItem.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.video_file:
            self.video_file.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)


class SocialHandle(models.Model):
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    display_name = models.CharField(max_length=100, help_text="e.g. Kesley")
    username = models.CharField(max_length=100, help_text="e.g. @kesley")
    url = models.URLField()
    followers = models.CharField(max_length=30, blank=True)
    followers_count = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)
    show_in_nav = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.get_platform_display()} — {self.username}"

    @classmethod
    def aggregate_engagement(cls):
        # Total reach should count every platform's followers, not just TikTok.
        total_followers = cls.objects.aggregate(total=models.Sum("followers_count"))["total"] or 0

        # Likes/comments/shares/views are only fetched for TikTok posts, so the
        # engagement RATE stays TikTok-specific — only the follower total is global.
        totals = cls.objects.filter(platform="tiktok").aggregate(
            likes=models.Sum("total_likes"),
            comments=models.Sum("total_comments"),
            shares=models.Sum("total_shares"),
            views=models.Sum("total_views"),
        )
        total_likes = totals["likes"] or 0
        total_comments = totals["comments"] or 0
        total_shares = totals["shares"] or 0
        total_views = totals["views"] or 0

        if total_views > 0:
            rate = (total_likes + total_comments + total_shares) / total_views * 100
        else:
            rate = 0

        if total_followers > 0:
            follower_rate = (total_likes + total_comments + total_shares) / total_followers * 100
        else:
            follower_rate = 0

        return {
            "total_followers": total_followers,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_views": total_views,
            "rate": round(rate, 1),
            "follower_rate": round(follower_rate, 1),
        }


class RateItem(models.Model):
    deliverable = models.CharField(max_length=200)
    platform = models.CharField(max_length=100)
    starting_price = models.CharField(max_length=60, help_text="e.g. KSh 80,000 or Custom quote")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.deliverable


class RateAddon(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class ContactSubmission(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("negotiating", "Negotiating"),
        ("closed", "Closed"),
        ("rejected", "Rejected"),
    ]
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200, blank=True)
    email = models.EmailField()
    collab_type = models.CharField(max_length=100)
    budget = models.CharField(max_length=100)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.name} ({self.email}) — {self.submitted_at:%Y-%m-%d}"


# ── Campaign Module ───────────────────────────────────────────

CAMPAIGN_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("active", "Active"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]

PAYMENT_STATUS_CHOICES = [
    ("unpaid", "Unpaid"),
    ("partial", "Partial"),
    ("paid", "Paid"),
]

CONTENT_TYPE_CHOICES = [
    ("video", "Video"),
    ("reel", "Reel"),
    ("story", "Story"),
    ("post", "Post"),
    ("live", "Live"),
    ("short", "Short"),
]

CURRENCY_CHOICES = [
    ("KES", "KES"),
    ("USD", "USD"),
    ("EUR", "EUR"),
    ("GBP", "GBP"),
]


class Campaign(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, related_name="campaigns")
    campaign_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default="draft")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default="KES")
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default="unpaid"
    )
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        brand_name = self.brand.name if self.brand else "No Brand"
        return f"{brand_name} — {self.campaign_name}"

    @property
    def remaining_balance(self):
        return self.payment_amount - self.deposit_amount

    @property
    def total_required(self):
        return sum(d.required_quantity for d in self.deliverables.all())

    @property
    def total_completed(self):
        return self.posts.count()

    @property
    def progress_percent(self):
        if self.total_required == 0:
            return 0
        return min(round((self.total_completed / self.total_required) * 100), 100)


class CampaignDeliverable(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="deliverables")
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    required_quantity = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"{self.get_platform_display()} {self.get_content_type_display()} x{self.required_quantity}"


class CampaignPost(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="posts")
    deliverable = models.ForeignKey(
        CampaignDeliverable, on_delete=models.SET_NULL, null=True, blank=True
    )
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, blank=True)
    post_url = models.URLField(blank=True)
    caption = models.TextField(blank=True)
    posting_date = models.DateField(null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["posting_date", "created_at"]

    def __str__(self):
        return f"{self.get_platform_display()} post — {self.campaign}"


class CampaignChecklist(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="checklist")
    item = models.CharField(max_length=300)
    is_done = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.item
