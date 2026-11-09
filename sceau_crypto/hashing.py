"""Empreintes par blocs : SHA-256 et SHA-512 calculés en une seule passe."""
import hashlib
import hmac
from dataclasses import dataclass
from typing import BinaryIO, Optional

CHUNK_SIZE = 1024 * 1024  # 1 Mio : le fichier n'est jamais chargé en entier


class FileTooLarge(Exception):
    """Le flux dépasse la taille maximale autorisée."""


@dataclass(frozen=True)
class Digests:
    sha256: str
    sha512: str
    size: int


def hash_stream(stream: BinaryIO, max_size: Optional[int] = None) -> Digests:
    """Lit le flux bloc par bloc. La limite est contrôlée pendant la lecture."""
    h256, h512, size = hashlib.sha256(), hashlib.sha512(), 0
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            break
        size += len(chunk)
        if max_size is not None and size > max_size:
            raise FileTooLarge(f"Taille maximale dépassée ({max_size} octets).")
        h256.update(chunk)
        h512.update(chunk)
    return Digests(h256.hexdigest(), h512.hexdigest(), size)


def hash_file(path, max_size: Optional[int] = None) -> Digests:
    with open(path, "rb") as f:
        return hash_stream(f, max_size)


def digests_equal(a: str, b: str) -> bool:
    """Comparaison en temps constant (bonne pratique, même pour un hash public)."""
    return hmac.compare_digest(a.lower().encode("ascii", "replace"),
                               b.lower().encode("ascii", "replace"))
