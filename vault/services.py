"""Logique métier du coffre : enregistrer un fichier, le vérifier."""
import re

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction

from audit.models import AuditEvent
from audit.services import record_event
from sceau_crypto.hashing import digests_equal, hash_stream

from .models import FileRecord, Verification

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def clean_filename(name) -> str:
    """Nom sûr à afficher : sans chemin, sans caractères de contrôle, 255 caractères max."""
    name = (name or "").replace("\\", "/").split("/")[-1]
    name = _CONTROL_CHARS.sub("", name).strip()
    if name in ("", ".", ".."):
        return "fichier"
    return name[:255]


def register_file(*, user, stream, filename) -> FileRecord:
    """Calcule l'empreinte (par blocs, taille limitée) et enregistre la référence.
    Le fichier lui-même n'est jamais conservé."""
    digests = hash_stream(stream, max_size=settings.SCEAU_MAX_UPLOAD_BYTES)
    name = clean_filename(filename)
    with transaction.atomic():
        record = FileRecord.objects.create(
            owner=user, filename=name, size=digests.size,
            sha256=digests.sha256, sha512=digests.sha512)
        record_event(user=user, type=AuditEvent.Type.RECORD_CREATED,
                     record=record, filename=name)
    return record


def verify_file(*, user, record, stream) -> Verification:
    """Compare un fichier à sa référence. Seul le propriétaire peut vérifier."""
    if record.owner_id != user.pk:
        raise PermissionDenied
    digests = hash_stream(stream, max_size=settings.SCEAU_MAX_UPLOAD_BYTES)
    identical = (digests.size == record.size
                 and digests_equal(record.sha256, digests.sha256)
                 and digests_equal(record.sha512, digests.sha512))
    result = Verification.Result.IDENTICAL if identical else Verification.Result.MODIFIED
    with transaction.atomic():
        verification = Verification.objects.create(
            record=record, observed_sha256=digests.sha256, result=result)
        record_event(user=user, type=AuditEvent.Type.VERIFICATION, record=record,
                     filename=record.filename, details={"result": result.value})
    return verification
