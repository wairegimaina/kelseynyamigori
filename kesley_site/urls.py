from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


def healthz(request):
    """Ultra-light liveness endpoint for uptime pingers (UptimeRobot).

    Deliberately touches NO database, session, or auth — so keeping the
    Render service warm does NOT keep the Neon compute awake. Point your
    UptimeRobot monitor at /healthz instead of the homepage.
    """
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path(f"{settings.CONTROL_PREFIX}/", include("control.urls")),
    path("", include("core.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
