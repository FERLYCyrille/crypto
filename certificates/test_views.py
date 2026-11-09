import io
import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from vault import services as vault

from .models import Certificate
from .testing import TempKeysMixin

User = get_user_model()
CONTENT = b"contenu du rapport"


class CertificateViewTests(TempKeysMixin, TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.user = User.objects.create_user("amina@example.com", password="x" * 12,
                                             first_name="Amina K.")
        self.other = User.objects.create_user("autre@example.com", password="x" * 12)
        self.client.force_login(self.user)
        self.record = vault.register_file(user=self.user, stream=io.BytesIO(CONTENT),
                                          filename="rapport.pdf")
        self.public = Client()

    def issue(self):
        r = self.client.post(reverse("certify", args=[self.record.pk]))
        return Certificate.objects.get(), r

    def public_check(self, cert_bytes, content=CONTENT):
        return self.public.post(reverse("public_verify"), {
            "file": SimpleUploadedFile("rapport.pdf", content),
            "certificate": SimpleUploadedFile("cert.json", cert_bytes)})

    def test_emission_et_page_du_certificat(self):
        cert, r = self.issue()
        self.assertRedirects(r, reverse("certificate_detail", args=[cert.pk]),
                             fetch_redirect_response=False)
        page = self.client.get(reverse("certificate_detail", args=[cert.pk]))
        self.assertContains(page, cert.serial)
        self.assertContains(self.client.get(reverse("certificate_list")), cert.serial)

    def test_telechargement_puis_verification_publique_sans_compte(self):
        cert, _ = self.issue()
        dl = self.client.get(reverse("certificate_download", args=[cert.pk]))
        self.assertIn("attachment", dl["Content-Disposition"])
        r = self.public_check(dl.content)
        self.assertContains(r, "Fichier intact, certifié par Amina K.")

    def test_fichier_modifie(self):
        cert, _ = self.issue()
        dl = self.client.get(reverse("certificate_download", args=[cert.pk]))
        self.assertContains(self.public_check(dl.content, b"falsifie"), "le fichier a été modifié")

    def test_certificat_altere_ou_illisible(self):
        cert, _ = self.issue()
        doc = json.loads(self.client.get(reverse("certificate_download", args=[cert.pk])).content)
        doc["payload"]["issuer"] = "Quelqu'un d'autre"
        for bad in (json.dumps(doc).encode(), b"pas du json"):
            self.assertContains(self.public_check(bad), "n'est pas authentique")

    def test_page_publique_accessible_sans_connexion(self):
        self.assertEqual(self.public.get(reverse("public_verify")).status_code, 200)
        self.assertEqual(self.public.get(reverse("public_key")).status_code, 200)

    def test_cle_publique_affichee(self):
        page = self.public.get(reverse("public_key"))
        self.assertContains(page, "BEGIN PUBLIC KEY")
        self.assertContains(page, "test-key")
        self.assertNotContains(page, "PRIVATE")

    def test_un_autre_utilisateur_n_accede_pas_au_certificat(self):
        cert, _ = self.issue()
        c = Client()
        c.force_login(self.other)
        self.assertEqual(c.get(reverse("certificate_detail", args=[cert.pk])).status_code, 404)
        self.assertEqual(c.get(reverse("certificate_download", args=[cert.pk])).status_code, 404)
        self.assertNotContains(c.get(reverse("certificate_list")), cert.serial)

    def test_limitation_de_la_verification_publique(self):
        codes = [self.public.post(reverse("public_verify"), {}).status_code for _ in range(21)]
        self.assertEqual(codes[-1], 429)
        self.assertNotIn(429, codes[:20])
