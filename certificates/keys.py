"""Chargement des clés de signature depuis le disque (jamais depuis la base)."""
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from sceau_crypto import signing


@lru_cache(maxsize=1)
def get_signing_key():
    path = settings.SCEAU_PRIVATE_KEY_PATH
    try:
        return signing.load_private_key(path.read_bytes())
    except OSError as exc:
        raise ImproperlyConfigured(f"Clé privée illisible : {path}") from exc


@lru_cache(maxsize=1)
def get_public_keys():
    """Retourne {identifiant de clé: clé publique}, après contrôle de cohérence."""
    path = settings.SCEAU_PUBLIC_KEY_PATH
    try:
        public = signing.load_public_key(path.read_bytes())
    except OSError as exc:
        raise ImproperlyConfigured(f"Clé publique illisible : {path}") from exc
    derived = get_signing_key().public_key()
    if signing.public_key_fingerprint(public) != signing.public_key_fingerprint(derived):
        raise ImproperlyConfigured("La clé publique ne correspond pas à la clé privée.")
    return {settings.SCEAU_KEY_ID: public}


def clear_key_cache():
    get_signing_key.cache_clear()
    get_public_keys.cache_clear()
