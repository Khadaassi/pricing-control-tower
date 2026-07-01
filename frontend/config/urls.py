from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from core.system_views import health_view, metrics_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("health", health_view, name="health"),
    path("metrics", metrics_view, name="metrics"),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]