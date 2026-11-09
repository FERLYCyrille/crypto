from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="vault_list", permanent=False)),
    path("", include("accounts.urls")),
    path("", include("vault.urls")),
    path("", include("certificates.urls")),
    path("", include("audit.urls")),
]
