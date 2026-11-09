import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from sceau_crypto import signing

from . import keys
from .models import Certificate


class KeyLoadingTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        priv, pub = signing.generate_keypair()
        (self.dir / "priv.pem").write_bytes(priv)
        (self.dir / "pub.pem").write_bytes(pub)
        self.override = override_settings(
            SCEAU_PRIVATE_KEY_PATH=self.dir / "priv.pem",
            SCEAU_PUBLIC_KEY_PATH=self.dir / "pub.pem", SCEAU_KEY_ID="test-key")
        self.override.enable()
        self.addCleanup(self.override.disable)
        keys.clear_key_cache()
        self.addCleanup(keys.clear_key_cache)

    def test_cles_chargees_et_coherentes(self):
        self.assertIn("test-key", keys.get_public_keys())
        sig = signing.sign(keys.get_signing_key(), b"m")
        self.assertTrue(signing.verify(keys.get_public_keys()["test-key"], b"m", sig))

    def test_paire_incoherente_refusee(self):
        (self.dir / "pub.pem").write_bytes(signing.generate_keypair()[1])
        keys.clear_key_cache()
        with self.assertRaises(ImproperlyConfigured):
            keys.get_public_keys()

    def test_cle_absente(self):
        (self.dir / "priv.pem").unlink()
        keys.clear_key_cache()
        with self.assertRaises(ImproperlyConfigured):
            keys.get_signing_key()


class CertificateModelTests(TestCase):
    def test_numero_de_serie(self):
        self.assertEqual(Certificate.serial_for(142, 2026), "SC-2026-000142")

    def test_creation(self):
        user = get_user_model().objects.create_user("a@example.com", password="x" * 12)
        c = Certificate.objects.create(owner=user, key_id="k", serial="SC-2026-000001",
                                       document={"payload": {}, "signature": "s"})
        self.assertEqual(str(c), "SC-2026-000001")
