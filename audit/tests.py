from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AuditEvent


class AuditEventTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("a@example.com", password="x" * 12)
        self.event = AuditEvent.objects.create(user=self.user, filename="a.pdf",
                                               type=AuditEvent.Type.RECORD_CREATED)

    def test_modification_interdite(self):
        self.event.filename = "autre.pdf"
        with self.assertRaises(PermissionError):
            self.event.save()

    def test_suppression_interdite(self):
        with self.assertRaises(PermissionError):
            self.event.delete()
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_evenement_survit_a_la_suppression_du_compte(self):
        self.user.delete()
        self.event.refresh_from_db()
        self.assertIsNone(self.event.user)
