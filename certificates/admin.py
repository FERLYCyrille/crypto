from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("serial", "owner", "key_id", "issued_at")
    readonly_fields = [f.name for f in Certificate._meta.fields]
