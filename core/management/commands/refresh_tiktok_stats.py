"""
core/management/commands/refresh_tiktok_stats.py
--------------------------------------------------
Re-fetches live view/like/comment counts for TikTok CampaignPosts.

Run manually:
    python manage.py refresh_tiktok_stats

Run for a specific month only (faster, matches the weekly report scope):
    python manage.py refresh_tiktok_stats --month 2026-07

Schedule it for true "automatic" updates — this project doesn't use Celery,
so the simplest option is a host-level cron job, e.g. on Render:
  Dashboard → New → Cron Job → command: `python manage.py refresh_tiktok_stats`
  → schedule e.g. "0 */6 * * *" (every 6 hours) or "0 6 * * *" (daily at 6am).
"""

from datetime import date
from calendar import monthrange

from django.core.management.base import BaseCommand, CommandError

from core.models import CampaignPost


class Command(BaseCommand):
    help = "Re-fetch live TikTok stats (views/likes/comments) for CampaignPost records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=str,
            default=None,
            help="Limit to a single month, format YYYY-MM. Defaults to ALL TikTok posts with a URL.",
        )

    def handle(self, *args, **options):
        from control.views import refresh_tiktok_stats_for_posts

        posts = CampaignPost.objects.filter(platform="tiktok").exclude(post_url="")

        month_arg = options.get("month")
        if month_arg:
            try:
                year_s, month_s = month_arg.split("-")
                year, month = int(year_s), int(month_s)
            except (ValueError, AttributeError):
                raise CommandError("--month must be in YYYY-MM format, e.g. 2026-07")
            start = date(year, month, 1)
            end = date(year, month, monthrange(year, month)[1])
            posts = posts.filter(posting_date__gte=start, posting_date__lte=end)

        total = posts.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No TikTok posts with links found to refresh."))
            return

        self.stdout.write(f"Refreshing {total} TikTok post(s)...")
        summary = refresh_tiktok_stats_for_posts(posts)

        self.stdout.write(self.style.SUCCESS(
            f"Done — updated {summary['updated']}, failed {summary['failed']}, skipped {summary['skipped']}."
        ))
        if summary["failed"]:
            self.stdout.write(self.style.WARNING(
                "Some posts failed to fetch — TikTok may be rate-limiting or blocking this server's IP. "
                "They'll be retried on the next run."
            ))
