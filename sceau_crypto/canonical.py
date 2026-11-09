"""JSON canonique : les octets signés doivent être identiques à la vérification."""
import json


def _check(value):
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _check(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Les clés d'un contenu signé doivent être des chaînes.")
            _check(item)
        return
    # Pas de float : leur sérialisation varie d'un langage à l'autre.
    raise TypeError(f"Type non autorisé dans un contenu signé : {type(value).__name__}")


def canonical_bytes(obj) -> bytes:
    """Clés triées, sans espaces, UTF-8."""
    _check(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
