from django.conf import settings
from django.db import models


class Certificate(models.Model):
    """Certificat émis. `document` contient le contenu signé, la signature et l'algorithme."""
    serial = models.CharField(max_length=24, unique=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="certificates")
    # Le certificat reste valable hors ligne même si la référence est supprimée.
    record = models.ForeignKey("vault.FileRecord", null=True, on_delete=models.SET_NULL,
                               related_name="certificates")
    key_id = models.CharField(max_length=64)
    document = models.JSONField(default=dict)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]

    @staticmethod
    def serial_for(pk: int, year: int) -> str:
        return f"SC-{year}-{pk:06d}"

    def __str__(self):
        return self.serial or f"Certificat #{self.pk}"
