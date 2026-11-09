from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

User = get_user_model()
GOOD = "motdepasse-solide-2026"


class GuideTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_guide_public(self):
        r = self.client.get(reverse("guide"))
        self.assertContains(r, "Guide d'utilisation")
        self.assertContains(r, "Créer un compte")
        self.assertNotContains(r, "Aller au coffre")

    def test_guide_connecte_propose_le_coffre(self):
        self.client.force_login(User.objects.create_user("a@example.com", password=GOOD))
        r = self.client.get(reverse("guide"))
        self.assertContains(r, "Aller au coffre")
        self.assertNotContains(r, "Créer un compte")

    def test_invitation_a_lire_le_guide_apres_connexion_une_seule_fois(self):
        User.objects.create_user("a@example.com", password=GOOD)
        r = self.client.post(reverse("login"), {"username": "a@example.com", "password": GOOD},
                             follow=True)
        self.assertContains(r, "Jetez un œil au guide")
        self.assertNotContains(self.client.get(reverse("vault_list")), "Jetez un œil")

    def test_invitation_apres_inscription(self):
        r = self.client.post(reverse("signup"), {"email": "b@example.com", "name": "B",
                                                 "password1": GOOD, "password2": GOOD}, follow=True)
        self.assertContains(r, "Jetez un œil au guide")

    def test_menu_burger_contient_le_compte_et_la_deconnexion(self):
        self.client.force_login(User.objects.create_user("a@example.com", password=GOOD,
                                                         first_name="Amina K."))
        page = self.client.get(reverse("vault_list")).content.decode()
        self.assertIn('aria-controls="menu"', page)
        menu = page.split('id="menu"')[1].split("</header>")[0]
        for expected in ("Amina K.", "a@example.com", "Se déconnecter", "Coffre", "Guide"):
            self.assertIn(expected, menu)

    def test_lien_guide_present_pour_les_visiteurs(self):
        self.assertContains(self.client.get(reverse("public_verify")),
                            f'href="{reverse("guide")}"')
