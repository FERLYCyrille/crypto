"""Émission et vérification des certificats d'intégrité."""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Optional

from .canonical import canonical_bytes
from .hashing import Digests, digests_equal
from .signing import sign, verify

CERT_VERSION = 1
REQUIRED_FIELDS = ("v", "serial", "filename", "size", "sha256", "sha512",
                   "issued_at", "issuer", "key_id")


class Verdict(str, Enum):
    INTACT = "intact"      # signature valide, fichier identique
    MODIFIED = "modified"  # signature valide, fichier différent
    INVALID = "invalid"    # certificat non authentique ou mal formé


@dataclass(frozen=True)
class VerificationResult:
    verdict: Verdict
    reason: str
    payload: Optional[dict] = None


def build_payload(*, serial: str, filename: str, size: int, sha256: str,
                  sha512: str, issued_at: datetime, issuer: str,
                  key_id: str) -> dict:
    if issued_at.tzinfo is None:
        raise ValueError("issued_at doit comporter un fuseau horaire.")
    utc = issued_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"v": CERT_VERSION, "serial": serial, "filename": filename,
            "size": size, "sha256": sha256.lower(), "sha512": sha512.lower(),
            "issued_at": utc, "issuer": issuer, "key_id": key_id}


def issue_certificate(payload: dict, private_key) -> dict:
    missing = [f for f in REQUIRED_FIELDS if f not in payload]
    if missing:
        raise ValueError(f"Champs manquants : {', '.join(missing)}")
    return {"payload": payload,
            "signature": sign(private_key, canonical_bytes(payload)),
            "alg": "Ed25519"}


def _invalid(reason: str) -> VerificationResult:
    return VerificationResult(Verdict.INVALID, reason)


def verify_certificate(certificate, public_keys: Mapping[str, object],
                       digests: Digests) -> VerificationResult:
    """Ordre voulu : structure, clé, SIGNATURE, puis seulement le hash.
    Le champ `alg` du certificat est ignoré : on n'accepte qu'Ed25519."""
    if not isinstance(certificate, dict):
        return _invalid("Certificat mal formé.")
    payload, signature = certificate.get("payload"), certificate.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature, str):
        return _invalid("Certificat mal formé.")
    if any(f not in payload for f in REQUIRED_FIELDS) or payload["v"] != CERT_VERSION:
        return _invalid("Certificat mal formé ou version inconnue.")
    key_id = payload["key_id"]
    key = public_keys.get(key_id) if isinstance(key_id, str) else None
    if key is None:
        return _invalid("Clé de signature inconnue.")
    try:
        message = canonical_bytes(payload)
    except (TypeError, RecursionError):
        return _invalid("Certificat mal formé.")
    if not verify(key, message, signature):
        return _invalid("Signature invalide.")
    same = (digests_equal(str(payload["sha256"]), digests.sha256)
            and digests_equal(str(payload["sha512"]), digests.sha512))
    if same:
        return VerificationResult(Verdict.INTACT, "Fichier identique au certifié.", payload)
    return VerificationResult(Verdict.MODIFIED, "Certificat authentique, fichier modifié.", payload)
