from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()
GOOD = "motdepasse-solide-2026"


class AuthTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_pages_protegees_redirigent_vers_la_connexion(self):
        for name in ("vault_list", "certificate_list", "history"):
            r = self.client.get(reverse(name))
            self.assertRedirects(r, f"{reverse('login')}?next={reverse(name)}",
                                 fetch_redirect_response=False)

    def test_inscription_puis_connexion_automatique(self):
        r = self.client.post(reverse("signup"), {
            "email": "Amina@Example.com", "name": "Amina K.",
            "password1": GOOD, "password2": GOOD})
        self.assertRedirects(r, reverse("vault_list"), fetch_redirect_response=False)
        user = User.objects.get()
        self.assertEqual((user.username, user.first_name), ("amina@example.com", "Amina K."))
        self.assertEqual(self.client.get(reverse("vault_list")).status_code, 200)

    def test_mot_de_passe_faible_refuse(self):
        r = self.client.post(reverse("signup"), {
            "email": "a@example.com", "name": "A", "password1": "password", "password2": "password"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_mots_de_passe_differents(self):
        r = self.client.post(reverse("signup"), {
            "email": "a@example.com", "name": "A", "password1": GOOD, "password2": GOOD + "x"})
        self.assertContains(r, "ne correspondent pas")

    def test_email_deja_utilise(self):
        User.objects.create_user("a@example.com", password=GOOD)
        r = self.client.post(reverse("signup"), {
            "email": "A@example.com", "name": "A", "password1": GOOD, "password2": GOOD})
        self.assertContains(r, "ne peut pas être utilisée")
        self.assertEqual(User.objects.count(), 1)

    def test_connexion_insensible_a_la_casse(self):
        User.objects.create_user("amina@example.com", password=GOOD)
        r = self.client.post(reverse("login"), {"username": "AMINA@Example.com", "password": GOOD})
        self.assertRedirects(r, "/coffre", fetch_redirect_response=False)

    def test_mauvais_mot_de_passe(self):
        User.objects.create_user("amina@example.com", password=GOOD)
        r = self.client.post(reverse("login"), {"username": "amina@example.com", "password": "non"})
        self.assertContains(r, "incorrect")

    def test_deconnexion_en_post_seulement(self):
        self.client.force_login(User.objects.create_user("a@example.com", password=GOOD))
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)
        self.assertEqual(self.client.get(reverse("vault_list")).status_code, 302)

    def test_csrf_actif(self):
        c = Client(enforce_csrf_checks=True)
        r = c.post(reverse("login"), {"username": "a@example.com", "password": GOOD})
        self.assertEqual(r.status_code, 403)

    def test_limitation_des_tentatives_de_connexion(self):
        codes = [self.client.post(reverse("login"), {"username": "x@example.com",
                                                      "password": "x"}).status_code
                 for _ in range(11)]
        self.assertEqual(codes[-1], 429)
        self.assertNotIn(429, codes[:10])
