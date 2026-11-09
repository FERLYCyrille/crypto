import hashlib, io, json, os, sys, unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sceau_crypto import canonical, certificate, hashing, signing
from sceau_crypto.certificate import Verdict


class HashingTests(unittest.TestCase):
    def test_vecteurs_connus(self):
        d = hashing.hash_stream(io.BytesIO(b"abc"))
        self.assertEqual(d.sha256, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        self.assertTrue(d.sha512.startswith("ddaf35a193617aba"))
        self.assertEqual(d.size, 3)

    def test_fichier_vide(self):
        d = hashing.hash_stream(io.BytesIO(b""))
        self.assertEqual(d.sha256, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_plusieurs_blocs(self):
        data = os.urandom(hashing.CHUNK_SIZE * 3 + 123)
        d = hashing.hash_stream(io.BytesIO(data))
        self.assertEqual(d.sha256, hashlib.sha256(data).hexdigest())
        self.assertEqual(d.sha512, hashlib.sha512(data).hexdigest())
        self.assertEqual(d.size, len(data))

    def test_taille_max_pendant_la_lecture(self):
        with self.assertRaises(hashing.FileTooLarge):
            hashing.hash_stream(io.BytesIO(b"x" * 100), max_size=99)
        hashing.hash_stream(io.BytesIO(b"x" * 100), max_size=100)

    def test_comparaison(self):
        self.assertTrue(hashing.digests_equal("ABCD", "abcd"))
        self.assertFalse(hashing.digests_equal("abcd", "abce"))
        self.assertFalse(hashing.digests_equal("abcd", "abcde"))


class CanonicalTests(unittest.TestCase):
    def test_ordre_des_cles_sans_effet(self):
        self.assertEqual(canonical.canonical_bytes({"b": 1, "a": 2}),
                         canonical.canonical_bytes({"a": 2, "b": 1}))

    def test_format(self):
        self.assertEqual(canonical.canonical_bytes({"b": [1, True], "a": "é"}),
                         '{"a":"é","b":[1,true]}'.encode("utf-8"))

    def test_refuse_les_flottants(self):
        with self.assertRaises(TypeError):
            canonical.canonical_bytes({"a": 1.5})


class SigningTests(unittest.TestCase):
    def setUp(self):
        priv, pub = signing.generate_keypair()
        self.priv, self.pub = signing.load_private_key(priv), signing.load_public_key(pub)

    def test_aller_retour(self):
        sig = signing.sign(self.priv, b"message")
        self.assertTrue(signing.verify(self.pub, b"message", sig))

    def test_message_modifie(self):
        sig = signing.sign(self.priv, b"message")
        self.assertFalse(signing.verify(self.pub, b"message!", sig))

    def test_mauvaise_cle(self):
        other = signing.load_public_key(signing.generate_keypair()[1])
        self.assertFalse(signing.verify(other, b"m", signing.sign(self.priv, b"m")))

    def test_signatures_absurdes(self):
        for bad in ("", "AAAA", "!!!", None, 42):
            self.assertFalse(signing.verify(self.pub, b"m", bad))

    def test_empreinte_de_cle_stable(self):
        self.assertEqual(signing.public_key_fingerprint(self.pub),
                         signing.public_key_fingerprint(self.pub))
        self.assertEqual(len(signing.public_key_fingerprint(self.pub)), 16)


class CertificateTests(unittest.TestCase):
    KID = "sceau-2026-1"

    def setUp(self):
        priv, pub = signing.generate_keypair()
        self.priv = signing.load_private_key(priv)
        self.keys = {self.KID: signing.load_public_key(pub)}
        self.content = b"contenu du rapport"
        self.d = hashing.hash_stream(io.BytesIO(self.content))
        payload = certificate.build_payload(
            serial="SC-2026-000142", filename="rapport-final.pdf", size=self.d.size,
            sha256=self.d.sha256, sha512=self.d.sha512,
            issued_at=datetime(2026, 11, 7, 14, 32, tzinfo=timezone.utc),
            issuer="Amina K.", key_id=self.KID)
        self.cert = certificate.issue_certificate(payload, self.priv)

    def check(self, cert, digests=None):
        return certificate.verify_certificate(cert, self.keys, digests or self.d)

    def test_fichier_intact(self):
        r = self.check(self.cert)
        self.assertEqual(r.verdict, Verdict.INTACT)
        self.assertEqual(r.payload["serial"], "SC-2026-000142")

    def test_fichier_modifie(self):
        other = hashing.hash_stream(io.BytesIO(b"contenu falsifie"))
        r = self.check(self.cert, other)
        self.assertEqual(r.verdict, Verdict.MODIFIED)
        self.assertIsNotNone(r.payload)

    def test_serialisation_json_stable(self):
        cert = json.loads(json.dumps(self.cert, indent=2, ensure_ascii=False))
        self.assertEqual(self.check(cert).verdict, Verdict.INTACT)

    def test_contenu_du_certificat_modifie(self):
        self.cert["payload"]["issuer"] = "Autre personne"
        self.assertEqual(self.check(self.cert).verdict, Verdict.INVALID)

    def test_attaque_fichier_et_hash_remplaces(self):
        fake = hashing.hash_stream(io.BytesIO(b"contenu falsifie"))
        self.cert["payload"]["sha256"] = fake.sha256
        self.cert["payload"]["sha512"] = fake.sha512
        self.assertEqual(self.check(self.cert, fake).verdict, Verdict.INVALID)

    def test_signature_alteree(self):
        sig = self.cert["signature"]
        self.cert["signature"] = ("A" if sig[0] != "A" else "B") + sig[1:]
        self.assertEqual(self.check(self.cert).verdict, Verdict.INVALID)

    def test_signee_par_une_autre_cle(self):
        rogue = signing.load_private_key(signing.generate_keypair()[0])
        forged = certificate.issue_certificate(self.cert["payload"], rogue)
        self.assertEqual(self.check(forged).verdict, Verdict.INVALID)

    def test_cle_inconnue(self):
        self.cert["payload"]["key_id"] = "inconnue"
        self.assertEqual(self.check(self.cert).verdict, Verdict.INVALID)

    def test_champ_alg_ignore(self):
        self.cert["signature"] = "AAAA"
        self.cert["alg"] = "none"
        self.assertEqual(self.check(self.cert).verdict, Verdict.INVALID)

    def test_certificats_mal_formes(self):
        for bad in (None, "texte", [], {}, {"payload": {}, "signature": "x"},
                    {"payload": "x", "signature": "x"}):
            self.assertEqual(self.check(bad).verdict, Verdict.INVALID)
        broken = json.loads(json.dumps(self.cert))
        del broken["payload"]["sha512"]
        self.assertEqual(self.check(broken).verdict, Verdict.INVALID)

    def test_date_sans_fuseau_refusee(self):
        with self.assertRaises(ValueError):
            certificate.build_payload(serial="s", filename="f", size=1, sha256="a",
                                      sha512="b", issued_at=datetime(2026, 1, 1),
                                      issuer="i", key_id="k")

    def test_date_convertie_en_utc(self):
        p = certificate.build_payload(
            serial="s", filename="f", size=1, sha256="a", sha512="b",
            issued_at=datetime(2026, 11, 7, 15, 32, tzinfo=timezone(timedelta(hours=1))),
            issuer="i", key_id="k")
        self.assertEqual(p["issued_at"], "2026-11-07T14:32:00Z")


if __name__ == "__main__":
    unittest.main()
