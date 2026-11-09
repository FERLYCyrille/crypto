from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Événement du journal. Ajout seul : ni modification ni suppression par le modèle."""

    class Type(models.TextChoices):
        RECORD_CREATED = "record_created", "Enregistrement"
        VERIFICATION = "verification", "Vérification"
        CERTIFICATE_ISSUED = "certificate_issued", "Certificat émis"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                             on_delete=models.SET_NULL, related_name="audit_events")
    type = models.CharField(max_length=30, choices=Type.choices)
    record = models.ForeignKey("vault.FileRecord", null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="audit_events")
    filename = models.CharField(max_length=255, blank=True)  # copie : survit à la référence
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError("Le journal d'audit est en ajout seul.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Le journal d'audit est en ajout seul.")

    def __str__(self):
        return f"{self.get_type_display()} · {self.filename}"
