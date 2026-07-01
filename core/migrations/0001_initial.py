# Generated for kesley_site — single initial migration containing all models
from django.db import migrations, models
import django.db.models.deletion
import cloudinary_storage.storage
import core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SiteProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(default='KESLEY', max_length=100)),
                ('tagline', models.CharField(default='Creator & Influencer / Media Kit 2026', max_length=200)),
                ('bio_lead', models.CharField(default="I'm Kesley — content creator, lifestyle influencer, and digital storyteller.", max_length=300)),
                ('bio_body', models.TextField(default='', help_text='Paragraphs separated by newlines')),
                ('based_in', models.CharField(default='Nairobi, Kenya', max_length=100)),
                ('content_types', models.CharField(default='Lifestyle · Fashion · Beauty · Vlogs', max_length=200)),
                ('contact_email', models.EmailField(default='hello@kesley.co.ke', max_length=254)),
                ('contact_phone', models.CharField(blank=True, max_length=50)),
                ('hero_image', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.MediaCloudinaryStorage(), upload_to='hero/')),
                ('portrait_caption', models.CharField(blank=True, default='', max_length=200)),
                ('footer_copy', models.CharField(default='© 2026 Kesley. All rights reserved.', max_length=200)),
                ('about_lead_text', models.CharField(default='', max_length=200)),
                ('about_paragraph_1', models.TextField(blank=True, default='')),
                ('about_paragraph_2', models.TextField(blank=True, default='')),
                ('about_paragraph_3', models.TextField(blank=True, default='')),
            ],
            options={'verbose_name': 'Site Profile'},
        ),
        migrations.CreateModel(
            name='Stat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=60)),
                ('value', models.CharField(help_text='e.g. 700 or 8.4', max_length=20)),
                ('suffix', models.CharField(blank=True, help_text='e.g. K+ or .4%', max_length=20)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('is_decimal', models.BooleanField(default=False, help_text='Animate as decimal?')),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('category', models.CharField(blank=True, help_text='e.g. Beauty & Skincare', max_length=100)),
                ('logo', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.MediaCloudinaryStorage(), upload_to='brands/')),
                ('url', models.URLField(blank=True)),
                ('rotation', models.FloatField(default=0, help_text='CSS tilt in degrees (-3 to 3)')),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='AboutImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(storage=cloudinary_storage.storage.MediaCloudinaryStorage(), upload_to='about/')),
                ('alt_text', models.CharField(blank=True, max_length=200)),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='WorkCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('slug', models.SlugField(help_text='Filter key e.g. fashion', unique=True)),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'ordering': ['order'], 'verbose_name': 'Work Category', 'verbose_name_plural': 'Work Categories'},
        ),
        migrations.CreateModel(
            name='WorkItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.workcategory')),
                ('title', models.CharField(max_length=200)),
                ('client', models.CharField(blank=True, max_length=100)),
                ('meta_label', models.CharField(blank=True, help_text='e.g. Fashion · TikTok', max_length=100)),
                ('video_file', models.FileField(blank=True, help_text='Upload MP4/MOV directly (max 10MB)', null=True, storage=cloudinary_storage.storage.VideoMediaCloudinaryStorage(), upload_to='work/videos/', validators=[core.models.validate_video_size])),
                ('video_embed_url', models.URLField(blank=True, help_text='YouTube/TikTok embed URL')),
                ('thumbnail', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.MediaCloudinaryStorage(), upload_to='work/thumbs/', validators=[core.models.validate_image_size])),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('post_url', models.URLField(blank=True, help_text='Link to the live TikTok/Instagram post')),
                ('engagement', models.CharField(blank=True, max_length=60)),
                ('post_views', models.PositiveIntegerField(default=0)),
                ('post_likes', models.PositiveIntegerField(default=0)),
                ('post_comments', models.PositiveIntegerField(default=0)),
                ('post_date', models.DateField(blank=True, null=True)),
                ('stats_fetched_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={'ordering': ['category__order', 'order']},
        ),
        migrations.CreateModel(
            name='SocialHandle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('instagram', 'Instagram'), ('tiktok', 'TikTok'), ('facebook', 'Facebook'), ('youtube', 'YouTube'), ('twitter', 'X / Twitter'), ('snapchat', 'Snapchat'), ('pinterest', 'Pinterest'), ('linkedin', 'LinkedIn'), ('threads', 'Threads'), ('whatsapp', 'WhatsApp')], max_length=30)),
                ('display_name', models.CharField(help_text='e.g. Kesley', max_length=100)),
                ('username', models.CharField(help_text='e.g. @kesley', max_length=100)),
                ('url', models.URLField()),
                ('followers', models.CharField(blank=True, max_length=30)),
                ('followers_count', models.PositiveIntegerField(default=0)),
                ('total_likes', models.PositiveIntegerField(default=0)),
                ('total_views', models.PositiveIntegerField(default=0)),
                ('total_comments', models.PositiveIntegerField(default=0)),
                ('total_shares', models.PositiveIntegerField(default=0)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('show_in_nav', models.BooleanField(default=True)),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='RateItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deliverable', models.CharField(max_length=200)),
                ('platform', models.CharField(max_length=100)),
                ('starting_price', models.CharField(help_text='e.g. KSh 80,000 or Custom quote', max_length=60)),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='RateAddon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='ContactSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('brand', models.CharField(blank=True, max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('collab_type', models.CharField(max_length=100)),
                ('budget', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('read', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('new', 'New'), ('contacted', 'Contacted'), ('negotiating', 'Negotiating'), ('closed', 'Closed'), ('rejected', 'Rejected')], default='new', max_length=20)),
            ],
            options={'ordering': ['-submitted_at']},
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='campaigns', to='core.brand')),
                ('campaign_name', models.CharField(max_length=200)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('payment_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('currency', models.CharField(choices=[('KES', 'KES'), ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP')], default='KES', max_length=5)),
                ('payment_status', models.CharField(choices=[('unpaid', 'Unpaid'), ('partial', 'Partial'), ('paid', 'Paid')], default='unpaid', max_length=10)),
                ('deposit_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='CampaignDeliverable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliverables', to='core.campaign')),
                ('platform', models.CharField(choices=[('instagram', 'Instagram'), ('tiktok', 'TikTok'), ('facebook', 'Facebook'), ('youtube', 'YouTube'), ('twitter', 'X / Twitter'), ('snapchat', 'Snapchat'), ('pinterest', 'Pinterest'), ('linkedin', 'LinkedIn'), ('threads', 'Threads'), ('whatsapp', 'WhatsApp')], max_length=30)),
                ('content_type', models.CharField(choices=[('video', 'Video'), ('reel', 'Reel'), ('story', 'Story'), ('post', 'Post'), ('live', 'Live'), ('short', 'Short')], max_length=20)),
                ('required_quantity', models.PositiveSmallIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='CampaignPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='core.campaign')),
                ('deliverable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.campaigndeliverable')),
                ('platform', models.CharField(choices=[('instagram', 'Instagram'), ('tiktok', 'TikTok'), ('facebook', 'Facebook'), ('youtube', 'YouTube'), ('twitter', 'X / Twitter'), ('snapchat', 'Snapchat'), ('pinterest', 'Pinterest'), ('linkedin', 'LinkedIn'), ('threads', 'Threads'), ('whatsapp', 'WhatsApp')], max_length=30)),
                ('content_type', models.CharField(blank=True, choices=[('video', 'Video'), ('reel', 'Reel'), ('story', 'Story'), ('post', 'Post'), ('live', 'Live'), ('short', 'Short')], max_length=20)),
                ('post_url', models.URLField(blank=True)),
                ('caption', models.TextField(blank=True)),
                ('posting_date', models.DateField(blank=True, null=True)),
                ('views', models.PositiveIntegerField(default=0)),
                ('likes', models.PositiveIntegerField(default=0)),
                ('comments', models.PositiveIntegerField(default=0)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['posting_date', 'created_at']},
        ),
        migrations.CreateModel(
            name='CampaignChecklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist', to='core.campaign')),
                ('item', models.CharField(max_length=300)),
                ('is_done', models.BooleanField(default=False)),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'ordering': ['order']},
        ),
    ]
