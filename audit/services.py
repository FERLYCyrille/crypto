from .models import AuditEvent


def record_event(*, user, type, record=None, filename="", details=None):
    """Point d'entrée unique pour écrire dans le journal."""
    return AuditEvent.objects.create(user=user, type=type, record=record,
                                     filename=filename, details=details or {})
