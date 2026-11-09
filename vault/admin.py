from django.contrib import admin

from .models import FileRecord, Verification


@admin.register(FileRecord)
class FileRecordAdmin(admin.ModelAdmin):
    list_display = ("filename", "owner", "sha256", "created_at")
    readonly_fields = [f.name for f in FileRecord._meta.fields]


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ("record", "result", "performed_at")
    readonly_fields = [f.name for f in Verification._meta.fields]
