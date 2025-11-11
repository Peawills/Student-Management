from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("committee/", include("committee.urls")),
    path("academics/", include("academics.urls", namespace="academics")),
    path("portal/", include("portal.urls", namespace="portal")),
    path("", include(("records.urls", "records"), namespace="records")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
