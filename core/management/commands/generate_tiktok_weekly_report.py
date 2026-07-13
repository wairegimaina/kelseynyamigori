"""
core/management/commands/generate_tiktok_weekly_report.py
------------------------------------------------------------
Generates the TikTok Weekly Report PDF for the current month and saves it
as a permanent, dated snapshot (TikTokWeeklyReportSnapshot) — so you have a
real week-by-week historical record, separate from the live report (whose
numbers keep changing as views/likes/comments get refreshed).

Run manually:
    python manage.py generate_tiktok_weekly_report

Run for a specific month:
    python manage.py generate_tiktok_weekly_report --month 2026-07

SCHEDULE IT FOR EVERY SATURDAY
-------------------------------
This project doesn't use Celery, so the simplest way to run this
automatically is a host-level cron job.

On Render:
  Dashboard -> New -> Cron Job
  Command:  python manage.py generate_tiktok_weekly_report
  Schedule: 0 18 * * 6      (every Saturday at 18:00 UTC)

On a plain Linux server, add to crontab (`crontab -e`):
  0 18 * * 6 cd /path/to/project && /path/to/venv/bin/python manage.py generate_tiktok_weekly_report

Cron day-of-week: 0=Sunday ... 6=Saturday.
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Generate the TikTok Weekly Report PDF for a month and archive it as a snapshot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=str,
            default=None,
            help="Month to generate, format YYYY-MM. Defaults to the current month.",
        )

    def handle(self, *args, **options):
        from control.views import save_tiktok_weekly_snapshot

        month_arg = options.get("month")
        today = date.today()
        if month_arg:
            try:
                year_s, month_s = month_arg.split("-")
                year, month = int(year_s), int(month_s)
            except (ValueError, AttributeError):
                raise CommandError("--month must be in YYYY-MM format, e.g. 2026-07")
        else:
            year, month = today.year, today.month

        self.stdout.write(f"Generating TikTok weekly report for {year:04d}-{month:02d}...")
        snapshot = save_tiktok_weekly_snapshot(year, month, snapshot_date=today)

        self.stdout.write(self.style.SUCCESS(
            f"Saved snapshot for {today.isoformat()} — "
            f"{snapshot.posts_count} posts, {snapshot.views_total:,} views, "
            f"{snapshot.likes_total:,} likes, {snapshot.comments_total:,} comments."
        ))
