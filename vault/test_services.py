import hashlib
import io

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings

from audit.models import AuditEvent
from sceau_crypto.hashing import FileTooLarge

from . import services
from .models import FileRecord, Verification


class CleanFilenameTests(TestCase):
    def test_cas_courants(self):
        c = services.clean_filename
        self.assertEqual(c("../../etc/passwd"), "passwd")
        self.assertEqual(c("C:\\docs\\rapport.pdf"), "rapport.pdf")
        self.assertEqual(c("a\x00b\n.pdf"), "ab.pdf")
        self.assertEqual(c(""), "fichier")
        self.assertEqual(c(None), "fichier")
        self.assertEqual(c(".."), "fichier")
        self.assertEqual(len(c("x" * 400)), 255)


class VaultServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("amina@example.com", password="x" * 12)
        self.other = User.objects.create_user("autre@example.com", password="x" * 12)
        self.content = b"contenu du rapport"

    def register(self, content=None):
        return services.register_file(user=self.user, stream=io.BytesIO(content or self.content),
                                      filename="rapport.pdf")

    def test_enregistrement(self):
        r = self.register()
        self.assertEqual(r.sha256, hashlib.sha256(self.content).hexdigest())
        self.assertEqual(r.sha512, hashlib.sha512(self.content).hexdigest())
        self.assertEqual(r.size, len(self.content))
        self.assertEqual(AuditEvent.objects.filter(type=AuditEvent.Type.RECORD_CREATED).count(), 1)

    @override_settings(SCEAU_MAX_UPLOAD_BYTES=10)
    def test_fichier_trop_gros_ne_laisse_aucune_trace(self):
        with self.assertRaises(FileTooLarge):
            self.register(b"x" * 11)
        self.assertEqual(FileRecord.objects.count(), 0)
        self.assertEqual(AuditEvent.objects.count(), 0)

    def test_verification_identique(self):
        r = self.register()
        v = services.verify_file(user=self.user, record=r, stream=io.BytesIO(self.content))
        self.assertEqual(v.result, Verification.Result.IDENTICAL)
        self.assertEqual(AuditEvent.objects.filter(type=AuditEvent.Type.VERIFICATION).count(), 1)

    def test_un_seul_octet_change_suffit(self):
        r = self.register()
        v = services.verify_file(user=self.user, record=r,
                                 stream=io.BytesIO(b"contenu du rapporT"))
        self.assertEqual(v.result, Verification.Result.MODIFIED)
        self.assertEqual(r.verifications.count(), 1)

    def test_un_autre_utilisateur_ne_peut_pas_verifier(self):
        r = self.register()
        with self.assertRaises(PermissionDenied):
            services.verify_file(user=self.other, record=r, stream=io.BytesIO(self.content))
        self.assertEqual(Verification.objects.count(), 0)
