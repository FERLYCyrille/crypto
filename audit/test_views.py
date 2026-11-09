import io

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from vault import services

User = get_user_model()


class HistoryViewTests(TestCase):
    def test_chacun_ne_voit_que_son_historique(self):
        a = User.objects.create_user("a@example.com", password="x" * 12)
        b = User.objects.create_user("b@example.com", password="x" * 12)
        services.register_file(user=a, stream=io.BytesIO(b"1"), filename="fichier-de-a.pdf")
        services.register_file(user=b, stream=io.BytesIO(b"2"), filename="fichier-de-b.pdf")
        self.client.force_login(a)
        page = self.client.get(reverse("history"))
        self.assertContains(page, "fichier-de-a.pdf")
        self.assertNotContains(page, "fichier-de-b.pdf")
