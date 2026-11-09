import uuid

from django.conf import settings
from django.db import models


class FileRecord(models.Model):
    """Référence d'un fichier : seule son empreinte est conservée, jamais le fichier."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="file_records")
    filename = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    sha512 = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["owner", "-created_at"])]

    def __str__(self):
        return f"{self.filename} ({self.sha256[:8]}…)"


class Verification(models.Model):
    """Résultat d'une vérification d'un fichier contre sa référence."""

    class Result(models.TextChoices):
        IDENTICAL = "identical", "Identique"
        MODIFIED = "modified", "Modifié"

    record = models.ForeignKey(FileRecord, on_delete=models.CASCADE,
                               related_name="verifications")
    observed_sha256 = models.CharField(max_length=64)
    result = models.CharField(max_length=10, choices=Result.choices)
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-performed_at"]

    def __str__(self):
        return f"{self.record.filename} : {self.get_result_display()}"
