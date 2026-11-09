import io

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from . import services
from .models import FileRecord

User = get_user_model()
CONTENT = b"contenu du rapport"


def upload(content=CONTENT, name="rapport.pdf"):
    return {"file": SimpleUploadedFile(name, content)}


class VaultViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("amina@example.com", password="x" * 12)
        self.other = User.objects.create_user("autre@example.com", password="x" * 12)
        self.client.force_login(self.user)
        self.record = services.register_file(user=self.user, stream=io.BytesIO(CONTENT),
                                             filename="rapport.pdf")

    def verify(self, content):
        return self.client.post(reverse("vault_verify", args=[self.record.pk]), upload(content))

    def test_depot_d_un_fichier(self):
        r = self.client.post(reverse("vault_list"), upload(b"autre", "notes.txt"))
        self.assertRedirects(r, reverse("vault_list"), fetch_redirect_response=False)
        self.assertEqual(FileRecord.objects.filter(owner=self.user).count(), 2)
        self.assertContains(self.client.get(reverse("vault_list")), "notes.txt")

    @override_settings(SCEAU_MAX_UPLOAD_BYTES=10)
    def test_fichier_trop_gros(self):
        r = self.client.post(reverse("vault_list"), upload(b"x" * 11))
        self.assertContains(r, "dépasse")
        self.assertEqual(FileRecord.objects.count(), 1)

    def test_aucun_fichier(self):
        r = self.client.post(reverse("vault_list"), {})
        self.assertContains(r, "Choisissez un fichier")

    def test_verification_identique(self):
        self.assertContains(self.verify(CONTENT), "identique à l'original")

    def test_verification_modifiee_surligne_la_difference(self):
        r = self.verify(b"contenu du rapporT")
        self.assertContains(r, "a changé")
        self.assertContains(r, "<mark>")
        self.assertContains(self.client.get(reverse("vault_list")), "Modifié")

    def test_les_autres_ne_voient_pas_mes_references(self):
        c = Client()
        c.force_login(self.other)
        self.assertNotContains(c.get(reverse("vault_list")), "rapport.pdf")
        self.assertEqual(c.get(reverse("vault_verify", args=[self.record.pk])).status_code, 404)
        self.assertEqual(c.post(reverse("certify", args=[self.record.pk])).status_code, 404)

    def test_certification_en_post_seulement(self):
        self.assertEqual(self.client.get(reverse("certify", args=[self.record.pk])).status_code, 405)

    def test_nom_de_fichier_malveillant_echappe(self):
        self.client.post(reverse("vault_list"), upload(b"x", "<img onerror=alert(1)>.txt"))
        page = self.client.get(reverse("vault_list")).content.decode()
        self.assertNotIn("<img onerror", page)
        self.assertIn("&lt;img onerror", page)
