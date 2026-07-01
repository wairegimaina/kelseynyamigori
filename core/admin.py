from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    SiteProfile, Stat, AboutImage, Brand,
    WorkCategory, WorkItem, SocialHandle,
    RateItem, RateAddon, ContactSubmission,
)
from django.conf import settings


admin.site.site_header = "Kesley — Site Admin"
admin.site.site_title  = "Kesley Admin"
admin.site.index_title = "Content Management"


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Identity', {
            'fields': ('display_name', 'tagline', 'footer_copy'),
        }),
        ('Hero Image', {
            'fields': ('hero_image', 'hero_preview'),
            'description': f'Max size: {settings.MAX_IMAGE_UPLOAD_SIZE // (1024*1024)} MB',
        }),
        ('Bio', {
            'fields': ('bio_lead', 'bio_body', 'based_in', 'content_types'),
        }),
        ('About Gallery Caption', {
            'fields': ('portrait_caption',),
        }),
        ('About Additional Content', {
            'fields': ('about_lead_text', 'about_paragraph_1', 'about_paragraph_2', 'about_paragraph_3'),
            'classes': ('collapse',),
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_phone'),
        }),
    )
    readonly_fields = ('hero_preview',)

    def hero_preview(self, obj):
        if obj and obj.hero_image:
            return mark_safe(
                f'<img src="{obj.hero_image.url}" style="max-height:180px;border-radius:8px;margin-top:6px;">'
            )
        return '—'
    hero_preview.short_description = 'Preview'

    def has_add_permission(self, request):
        return not SiteProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ('label', 'value', 'suffix', 'is_decimal', 'order')
    list_editable = ('order',)
    ordering = ('order',)


@admin.register(AboutImage)
class AboutImageAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'alt_text', 'order')
    list_editable = ('order',)
    readonly_fields = ('thumb',)
    ordering = ('order',)

    def thumb(self, obj):
        if obj and obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="height:48px;width:48px;object-fit:cover;border-radius:6px;border:1px solid #ddd;">'
            )
        return '—'
    thumb.short_description = ''


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('logo_preview', 'name', 'category', 'url_link', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'category')
    ordering = ('order',)

    def logo_preview(self, obj):
        if obj and obj.logo:
            return mark_safe(
                f'<img src="{obj.logo.url}" style="height:36px;max-width:80px;object-fit:contain;">'
            )
        return '—'
    logo_preview.short_description = 'Logo'

    def url_link(self, obj):
        if obj and obj.url:
            return mark_safe(f'<a href="{obj.url}" target="_blank">↗</a>')
        return '—'
    url_link.short_description = 'Link'

    def save_model(self, request, obj, form, change):
        if not change and Brand.objects.count() >= 15:
            self.message_user(request, "Maximum of 15 brands allowed.", level='error')
            return
        super().save_model(request, obj, form, change)


class WorkItemInline(admin.TabularInline):
    model = WorkItem
    extra = 0
    max_num = 3
    fields = ('title', 'client', 'meta_label', 'video_file', 'video_embed_url', 'thumbnail', 'order')
    show_change_link = True


@admin.register(WorkCategory)
class WorkCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'video_count', 'order')
    list_editable = ('order',)
    inlines = [WorkItemInline]
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)

    def video_count(self, obj):
        count = obj.items.count()
        colour = '#e74c3c' if count >= 3 else '#27ae60'
        return mark_safe(f'<span style="color:{colour};font-weight:600">{count}/3</span>')
    video_count.short_description = 'Videos'

    def save_model(self, request, obj, form, change):
        if not change and WorkCategory.objects.count() >= 4:
            self.message_user(request, "Maximum of 4 categories allowed.", level='error')
            return
        super().save_model(request, obj, form, change)


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'client', 'video_status', 'order')
    list_editable = ('order',)
    list_filter = ('category',)
    search_fields = ('title', 'client')
    ordering = ('category__order', 'order')

    def video_status(self, obj):
        if obj and obj.video_file:
            return mark_safe('<span style="color:#27ae60;font-weight:600">✔ Uploaded</span>')
        elif obj and obj.video_embed_url:
            return mark_safe('<span style="color:#b8922a;font-weight:600">✔ Embed URL</span>')
        return mark_safe('<span style="color:#e74c3c;font-weight:600">✘ None</span>')
    video_status.short_description = 'Video'

    def save_model(self, request, obj, form, change):
        if not change:
            if WorkItem.objects.filter(category=obj.category).count() >= 3:
                self.message_user(
                    request,
                    f'"{obj.category.name}" already has 3 videos. Remove one first.',
                    level='error',
                )
                return
        super().save_model(request, obj, form, change)


@admin.register(SocialHandle)
class SocialHandleAdmin(admin.ModelAdmin):
    list_display = ('platform_badge', 'display_name', 'username', 'followers', 'show_in_nav', 'order')
    list_editable = ('show_in_nav', 'order')
    ordering = ('order',)

    PLATFORM_COLOURS = {
        'instagram': '#C13584',
        'tiktok':    '#000000',
        'facebook':  '#1877F2',
        'youtube':   '#FF0000',
        'twitter':   '#1DA1F2',
        'snapchat':  '#FFFC00',
        'pinterest': '#E60023',
        'linkedin':  '#0A66C2',
        'threads':   '#000000',
        'whatsapp':  '#25D366',
    }

    def platform_badge(self, obj):
        colour = self.PLATFORM_COLOURS.get(obj.platform, '#888')
        return mark_safe(
            f'<span style="background:{colour};color:#fff;padding:2px 10px;'
            f'border-radius:20px;font-size:0.78em;font-weight:600">{obj.get_platform_display()}</span>'
        )
    platform_badge.short_description = 'Platform'


@admin.register(RateItem)
class RateItemAdmin(admin.ModelAdmin):
    list_display = ('deliverable', 'platform', 'starting_price', 'order')
    list_editable = ('order',)
    ordering = ('order',)


@admin.register(RateAddon)
class RateAddonAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)
    ordering = ('order',)


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name_with_read', 'email', 'brand', 'collab_type', 'budget', 'submitted_at', 'mark_read', 'status')
    list_filter = ('read', 'collab_type', 'status')
    list_editable = ('status',)
    search_fields = ('name', 'email', 'brand')
    ordering = ('-submitted_at',)
    readonly_fields = (
        'name', 'email', 'brand', 'collab_type',
        'budget', 'message', 'submitted_at',
    )
    fieldsets = (
        ('Sender', {
            'fields': ('name', 'email', 'brand'),
        }),
        ('Enquiry', {
            'fields': ('collab_type', 'budget', 'message'),
        }),
        ('Meta', {
            'fields': ('submitted_at', 'read', 'status'),
        }),
    )

    def name_with_read(self, obj):
        if obj and not obj.read:
            return mark_safe(f'<strong style="color:#2c3e50">{obj.name}</strong> 🔵')
        return obj.name if obj else '—'
    name_with_read.short_description = 'Name'

    def mark_read(self, obj):
        if obj and obj.read:
            return mark_safe('<span style="color:#27ae60;font-weight:600">✔ Read</span>')
        return mark_safe('<span style="color:#e74c3c;font-weight:600">● Unread</span>') if obj else '—'
    mark_read.short_description = 'Status'

    def has_add_permission(self, request):
        return False
from core.models import Campaign, CampaignDeliverable, CampaignPost, CampaignChecklist

class DeliverableInline(admin.TabularInline):
    model = CampaignDeliverable
    extra = 1

class PostInline(admin.TabularInline):
    model = CampaignPost
    extra = 0

class ChecklistInline(admin.TabularInline):
    model = CampaignChecklist
    extra = 1

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["campaign_name", "brand", "status", "payment_status", "payment_amount", "created_at"]
    list_filter = ["status", "payment_status"]
    inlines = [DeliverableInline, PostInline, ChecklistInline]
