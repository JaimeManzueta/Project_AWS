# imageapp/urls.py

# URL routing for the demo project.
# - Maps the tiny photo app (home + process)
# - Exposes Django admin
# - Adds a simple health check and a favicon shortcut (nice for demos)
# - Serves /static/ files automatically when DEBUG=True

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

# Import only what you need from your views (avoid wildcard imports)
from photoapp.views import home, process_view


def healthz(_request):
    """Lightweight health probe: GET /healthz -> 'ok'"""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # App routes
    path("", home, name="home"),
    path("process/", process_view, name="process"),

    # Dev helpers
    path("healthz/", healthz, name="healthz"),
    re_path(r"^favicon\.ico$", RedirectView.as_view(url="/static/favicon.ico", permanent=False)),
]

# Serve static files in DEBUG (use nginx in production)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=getattr(settings, "STATIC_ROOT", None))