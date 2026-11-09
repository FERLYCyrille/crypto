"""Logique métier des certificats : émettre, exporter, vérifier un certificat reçu."""
import json
import uuid

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction

from audit.models import AuditEvent
from audit.services import record_event
from sceau_crypto import certificate as cert_lib
from sceau_crypto.hashing import hash_stream

from . import keys
from .models import Certificate

MAX_CERTIFICATE_BYTES = 64 * 1024


def issue_certificate(*, user, record) -> Certificate:
    """Émet et signe un certificat pour une référence appartenant à `user`."""
    if record.owner_id != user.pk:
        raise PermissionDenied
    with transaction.atomic():
        # Numéro provisoire unique : le vrai numéro dépend de l'identifiant créé.
        cert = Certificate.objects.create(
            owner=user, record=record, key_id=settings.SCEAU_KEY_ID,
            serial=f"tmp-{uuid.uuid4().hex[:16]}")
        cert.serial = Certificate.serial_for(cert.pk, cert.issued_at.year)
        payload = cert_lib.build_payload(
            serial=cert.serial, filename=record.filename, size=record.size,
            sha256=record.sha256, sha512=record.sha512, issued_at=cert.issued_at,
            issuer=user.get_full_name() or user.get_username(), key_id=cert.key_id)
        cert.document = cert_lib.issue_certificate(payload, keys.get_signing_key())
        cert.save(update_fields=["serial", "document"])
        record_event(user=user, type=AuditEvent.Type.CERTIFICATE_ISSUED, record=record,
                     filename=record.filename, details={"serial": cert.serial})
    return cert


def certificate_bytes(cert: Certificate) -> bytes:
    """Contenu du fichier certificat à télécharger."""
    return json.dumps(cert.document, indent=2, ensure_ascii=False).encode("utf-8")


def read_certificate(stream):
    """Lit un certificat JSON de taille bornée. Retourne None si illisible."""
    data = stream.read(MAX_CERTIFICATE_BYTES + 1)
    if len(data) > MAX_CERTIFICATE_BYTES:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None


def verify_received(*, certificate_stream, file_stream):
    """Vérification publique : repose uniquement sur la signature, pas sur la base."""
    certificate = read_certificate(certificate_stream)
    digests = hash_stream(file_stream, max_size=settings.SCEAU_MAX_UPLOAD_BYTES)
    return cert_lib.verify_certificate(certificate, keys.get_public_keys(), digests)
