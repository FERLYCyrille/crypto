"""Aides de test : clés de signature temporaires."""
import tempfile
from pathlib import Path

from django.test import override_settings

from sceau_crypto import signing

from . import keys


class TempKeysMixin:
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        priv, pub = signing.generate_keypair()
        (Path(tmp.name) / "priv.pem").write_bytes(priv)
        (Path(tmp.name) / "pub.pem").write_bytes(pub)
        ov = override_settings(SCEAU_PRIVATE_KEY_PATH=Path(tmp.name) / "priv.pem",
                               SCEAU_PUBLIC_KEY_PATH=Path(tmp.name) / "pub.pem",
                               SCEAU_KEY_ID="test-key")
        ov.enable()
        self.addCleanup(ov.disable)
        keys.clear_key_cache()
        self.addCleanup(keys.clear_key_cache)
