from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import FileRecord, Verification


def make_record(owner, name="a.pdf"):
    return FileRecord.objects.create(owner=owner, filename=name, size=3,
                                     sha256="a" * 64, sha512="b" * 128)


class VaultModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("amina@example.com", password="x" * 12)
        self.other = User.objects.create_user("autre@example.com", password="x" * 12)

    def test_references_isolees_par_proprietaire(self):
        r = make_record(self.user)
        self.assertEqual(list(FileRecord.objects.filter(owner=self.user)), [r])
        self.assertFalse(FileRecord.objects.filter(owner=self.other).exists())

    def test_verification_rattachee_a_la_reference(self):
        r = make_record(self.user)
        Verification.objects.create(record=r, observed_sha256="c" * 64,
                                    result=Verification.Result.MODIFIED)
        self.assertEqual(r.verifications.count(), 1)

    def test_suppression_du_compte_supprime_ses_references(self):
        make_record(self.user)
        self.user.delete()
        self.assertEqual(FileRecord.objects.count(), 0)
