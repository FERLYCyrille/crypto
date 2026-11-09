import io
import json

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone

from audit.models import AuditEvent
from sceau_crypto.certificate import Verdict
from vault import services as vault

from . import services
from .models import Certificate
from .testing import TempKeysMixin


class CertificateServiceTests(TempKeysMixin, TestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.user = User.objects.create_user("amina@example.com", password="x" * 12,
                                             first_name="Amina", last_name="K.")
        self.other = User.objects.create_user("autre@example.com", password="x" * 12)
        self.content = b"contenu du rapport"
        self.record = vault.register_file(user=self.user, stream=io.BytesIO(self.content),
                                          filename="rapport-final.pdf")

    def check(self, cert_bytes, file_content=None):
        return services.verify_received(
            certificate_stream=io.BytesIO(cert_bytes),
            file_stream=io.BytesIO(self.content if file_content is None else file_content))

    def test_emission(self):
        c = services.issue_certificate(user=self.user, record=self.record)
        self.assertRegex(c.serial, rf"^SC-{timezone.now().year}-\d{{6}}$")
        self.assertEqual(c.document["payload"]["issuer"], "Amina K.")
        self.assertEqual(c.document["payload"]["filename"], "rapport-final.pdf")
        self.assertEqual(AuditEvent.objects.filter(
            type=AuditEvent.Type.CERTIFICATE_ISSUED).count(), 1)

    def test_numeros_distincts(self):
        a = services.issue_certificate(user=self.user, record=self.record)
        b = services.issue_certificate(user=self.user, record=self.record)
        self.assertNotEqual(a.serial, b.serial)
        self.assertFalse(Certificate.objects.filter(serial__startswith="tmp-").exists())

    def test_un_autre_utilisateur_ne_peut_pas_emettre(self):
        with self.assertRaises(PermissionDenied):
            services.issue_certificate(user=self.other, record=self.record)
        self.assertEqual(Certificate.objects.count(), 0)

    def test_parcours_complet_fichier_intact(self):
        c = services.issue_certificate(user=self.user, record=self.record)
        r = self.check(services.certificate_bytes(c))
        self.assertEqual(r.verdict, Verdict.INTACT)
        self.assertEqual(r.payload["serial"], c.serial)

    def test_parcours_complet_fichier_modifie(self):
        c = services.issue_certificate(user=self.user, record=self.record)
        r = self.check(services.certificate_bytes(c), b"contenu falsifie")
        self.assertEqual(r.verdict, Verdict.MODIFIED)

    def test_certificat_altere(self):
        c = services.issue_certificate(user=self.user, record=self.record)
        doc = json.loads(services.certificate_bytes(c))
        doc["payload"]["filename"] = "autre.pdf"
        r = self.check(json.dumps(doc).encode())
        self.assertEqual(r.verdict, Verdict.INVALID)

    def test_certificats_illisibles(self):
        for bad in (b"pas du json", b"\xff\xfe\x00", b"[]", b"null", b"",
                    b"[" * 50000 + b"]" * 50000, b"x" * (services.MAX_CERTIFICATE_BYTES + 1)):
            self.assertEqual(self.check(bad).verdict, Verdict.INVALID)
