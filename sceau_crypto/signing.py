"""Signature Ed25519 (bibliothèque `cryptography`)."""
import base64
import binascii
import hashlib

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

_PEM = serialization.Encoding.PEM


def generate_keypair() -> tuple[bytes, bytes]:
    """Retourne (clé privée PEM, clé publique PEM)."""
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        _PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public_pem = private.public_key().public_bytes(
        _PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return private_pem, public_pem


def load_private_key(pem: bytes) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("La clé n'est pas une clé Ed25519.")
    return key


def load_public_key(pem: bytes) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(pem)
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("La clé n'est pas une clé Ed25519.")
    return key


def public_key_fingerprint(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(serialization.Encoding.Raw,
                                  serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()[:16]


def sign(private_key: Ed25519PrivateKey, message: bytes) -> str:
    return base64.urlsafe_b64encode(private_key.sign(message)).decode("ascii")


def verify(public_key: Ed25519PublicKey, message: bytes, signature_b64) -> bool:
    """Ne lève jamais d'exception : toute entrée invalide donne False."""
    try:
        signature = base64.urlsafe_b64decode(signature_b64.encode("ascii"))
        public_key.verify(signature, message)
        return True
    except (InvalidSignature, binascii.Error, ValueError, TypeError,
            AttributeError, UnicodeEncodeError):
        return False
