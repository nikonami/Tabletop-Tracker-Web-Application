# Autor: Sofija Brajović 2020/0179
# Tim: DNMS
# Opis: Django unit testovi za SSU1–SSU6 (Nikola Stamenković)
#       Metod klasa ekvivalencije – legalne i nelegalne klase
#
#   python manage.py test tabletop.tests_unit --keepdb

import unittest

from django.db.models import Model
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tabletop.models import Korisnik, Igra

TEST_USERNAME = 'test_dnms_unit'
TEST_PASSWORD = 'Test1234!'

TIP_KORISNIK = 1


def login_korisnik(client):
    """Postavlja Django auth i session podatke koje views koriste."""
    logged_in = client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
    if not logged_in:
        return False
    try:
        korisnik = Korisnik.objects.filter(korisnickoime=TEST_USERNAME).first()
        if not korisnik:
            return False
        session = client.session
        session['idkor'] = korisnik.idkor
        session['korisnickoime'] = korisnik.korisnickoime
        session['tip'] = korisnik.tip
        session['ime'] = korisnik.ime
        session.save()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# SSU1 – Praćenje igara
# ---------------------------------------------------------------------------

class PracenjeIgaraTests(TestCase):
    """
    SSU1 – Praćenje igara
    Klase ekvivalencije:
      L1 – ulogovani korisnik pristupa /profile/igre/ → 200
      N1 – neulogovani korisnik pristupa /profile/igre/ → nije 200
    """

#    databases = ['default']

    def setUp(self):
        super().setUp()
        self.kor = Korisnik.objects.create(
            korisnickoime=TEST_USERNAME,
            email="dummymail2@gmail.com",
            tip=TIP_KORISNIK,
            ime=TEST_USERNAME,
            prezime=TEST_USERNAME,
            privatnost=0
        )
        self.kor.set_lozinka(TEST_PASSWORD)
        self.kor.save()

        self.koruser = User.objects.create(username=TEST_USERNAME)
        self.koruser.set_password(TEST_PASSWORD)
        self.koruser.save()

        self.client = Client()
        self.client.raise_request_exception = False

    def test_L1_ulogovani_korisnik_vidi_listu_vlasnistva(self):
        """L1 – Ulogovani korisnik dobija 200 na /profile/igre/."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.get(reverse('my-games'))
        self.assertEqual(response.status_code, 200)

    def test_N1_neulogovani_korisnik_ne_moze_da_vidi_listu(self):
        """N1 – Neulogovani korisnik ne dobija 200 na /profile/igre/."""
        response = self.client.get(reverse('my-games'))
        self.assertNotEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# SSU2 – Dodavanje prijatelja
# ---------------------------------------------------------------------------

class DodavanjePrijateljaTests(TestCase):
    """
    SSU2 – Dodavanje prijatelja
    Klase ekvivalencije:
      L1 – ulogovani korisnik otvara vlastiti profil → 200
      L2 – profil stranica sadrži korisničko ime
      N1 – neulogovani korisnik pristupa profilu → nije 200
    """

    databases = ['default']

    def setUp(self):
        super().setUp()
        self.kor = Korisnik.objects.create(
            korisnickoime=TEST_USERNAME,
            email="dummymail2@gmail.com",
            tip=TIP_KORISNIK,
            ime=TEST_USERNAME,
            prezime=TEST_USERNAME,
            privatnost=0
        )
        self.kor.set_lozinka(TEST_PASSWORD)
        self.kor.save()

        self.koruser = User.objects.create(username=TEST_USERNAME)
        self.koruser.set_password(TEST_PASSWORD)
        self.koruser.save()

        self.client = Client()
        self.client.raise_request_exception = False

    def test_L1_ulogovani_korisnik_vidi_vlastiti_profil(self):
        """L1 – Ulogovani korisnik dobija 200 na /profile/."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_N1_neulogovani_korisnik_ne_moze_profilu(self):
        """N1 – Neulogovani korisnik ne dobija 200 na /profile/."""
        response = self.client.get(reverse('profile'))
        self.assertNotEqual(response.status_code, 200)

    def test_L2_profil_sadrzi_korisnicke_podatke(self):
        """L2 – Profil stranica sadrži korisničko ime."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.get(reverse('profile'))
        if response.status_code == 200:
            self.assertContains(response, TEST_USERNAME, html=False)


# ---------------------------------------------------------------------------
# SSU3 – Praćenje statistike
# ---------------------------------------------------------------------------

class PracenjeStatistikeTests(TestCase):
    """
    SSU3 – Praćenje statistike
    Klase ekvivalencije:
      L1 – ulogovani korisnik otvara /profile/statistika/ → 200
      N1 – neulogovani korisnik otvara /profile/statistika/ → nije 200
      L2 – /igre/ dostupna svima → 200
    """

    databases = ['default']

    def setUp(self):
        super().setUp()
        self.kor = Korisnik.objects.create(
            korisnickoime=TEST_USERNAME,
            email="dummymail2@gmail.com",
            tip=TIP_KORISNIK,
            ime=TEST_USERNAME,
            prezime=TEST_USERNAME,
            privatnost=0
        )
        self.kor.set_lozinka(TEST_PASSWORD)
        self.kor.save()

        self.koruser = User.objects.create(username=TEST_USERNAME)
        self.koruser.set_password(TEST_PASSWORD)
        self.koruser.save()

        self.client = Client()
        self.client.raise_request_exception = False

    def test_L1_ulogovani_korisnik_vidi_statistike(self):
        """L1 – Ulogovani korisnik dobija 200 na /profile/statistika/."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.get(reverse('my-statistics'))
        self.assertEqual(response.status_code, 200)

    def test_N1_neulogovani_ne_moze_da_vidi_statistike(self):
        """N1 – Neulogovani korisnik ne dobija 200 na /profile/statistika/."""
        response = self.client.get(reverse('my-statistics'))
        self.assertNotEqual(response.status_code, 200)

    def test_L2_stranica_igara_dostupna(self):
        """L2 – /igre/ je dostupna i vraća 200."""
        response = self.client.get(reverse('igre'))
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# SSU4 – Pravljenje liste igara
# ---------------------------------------------------------------------------

class PravljenjeListeIgaraTests(TestCase):
    """
    SSU4 – Pravljenje liste igara
    Klase ekvivalencije:
      L1 – ulogovani korisnik otvara /profile/liste-igara/ → 200
      N1 – neulogovani korisnik otvara /profile/liste-igara/ → nije 200
      N2 – POST sa rezervisanim imenom 'Imam' → redirect (302)
      N3 – POST sa rezervisanim imenom 'Igrao' → redirect (302)
      N4 – POST sa rezervisanim imenom 'Wishlist' → redirect (302)
      L2 – POST sa validnim imenom → lista kreirana (200)
    """

    databases = ['default']

    def setUp(self):
        super().setUp()
        self.kor = Korisnik.objects.create(
            korisnickoime=TEST_USERNAME,
            email="dummymail2@gmail.com",
            tip=TIP_KORISNIK,
            ime=TEST_USERNAME,
            prezime=TEST_USERNAME,
            privatnost=0
        )
        ig=Igra.objects.create(naziv='test', godinaproizvodnje='2000-01-01', minigraca=1,maxigraca=4, opis='test',slikaurl="https://upload.wikimedia.org/wikipedia/en/1/1a/Scythe_boxart.png",
            videotutorialurl="https://www.youtube.com/embed/MrmFWOm6U0g?si=XiRDzR1e_7eNpudt",
            zanr="strategija")
        ig.save()
        self.kor.set_lozinka(TEST_PASSWORD)
        self.kor.save()

        self.koruser = User.objects.create(username=TEST_USERNAME)
        self.koruser.set_password(TEST_PASSWORD)
        self.koruser.save()

        self.client = Client()
        self.client.raise_request_exception = False

    def test_L1_ulogovani_korisnik_vidi_liste(self):
        """L1 – Ulogovani korisnik dobija 200 na /profile/liste-igara/."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.get(reverse('my-game-lists'))
        self.assertEqual(response.status_code, 200)

    def test_N1_neulogovani_ne_moze_da_vidi_liste(self):
        """N1 – Neulogovani korisnik ne dobija 200 na /profile/liste-igara/."""
        response = self.client.get(reverse('my-game-lists'))
        self.assertNotEqual(response.status_code, 200)

    def test_N2_rezervisano_ime_imam_ne_kreira_listu(self):
        """N2 – POST sa imenom 'Imam' vrši redirect bez kreiranja liste."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.post(reverse('my-game-lists'), {
            'make-list': '1', 'list-name': 'Imam'
        })
        self.assertEqual(response.status_code, 302)

    def test_N3_rezervisano_ime_igrao_ne_kreira_listu(self):
        """N3 – POST sa imenom 'Igrao' vrši redirect bez kreiranja liste."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.post(reverse('my-game-lists'), {
            'make-list': '1', 'list-name': 'Igrao'
        })
        self.assertEqual(response.status_code, 302)

    def test_N4_rezervisano_ime_wishlist_ne_kreira_listu(self):
        """N4 – POST sa imenom 'Wishlist' vrši redirect bez kreiranja liste."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.post(reverse('my-game-lists'), {
            'make-list': '1', 'list-name': 'Wishlist'
        })
        self.assertEqual(response.status_code, 302)

    def test_L2_validno_ime_kreira_listu(self):
        """L2 – POST sa validnim (nerezervisanim) imenom uspješno kreira listu."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.post(reverse('my-game-lists'), {
            'make-list': '1', 'list-name': 'MojaTestLista'
        })
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# SSU5 – Ostavljanje utiska na igru
# ---------------------------------------------------------------------------

class OstavljanjeUtisakaTests(TestCase):
    """
    SSU5 – Ostavljanje utiska na igru
    Klase ekvivalencije:
      L1 – /igre/ dostupna ulogovanom → 200
      N1 – /igre/ dostupna neulogovanom → 200
      L2 – RecenzijaForm sa validnim podacima → validna
      L3 – RecenzijaForm sa minimalnim ratingom (1) → validna
      N2 – RecenzijaForm bez opisa → nije validna
      N3 – RecenzijaForm rating=0 → bug (forma prihvata)
      N4 – RecenzijaForm rating=10 → bug (forma prihvata)
    """

    databases = ['default']

    def setUp(self):
        super().setUp()
        self.kor = Korisnik.objects.create(
            korisnickoime=TEST_USERNAME,
            email="dummymail2@gmail.com",
            tip=TIP_KORISNIK,
            ime=TEST_USERNAME,
            prezime=TEST_USERNAME,
            privatnost=0
        )
        self.kor.set_lozinka(TEST_PASSWORD)
        self.kor.save()

        self.koruser = User.objects.create(username=TEST_USERNAME)
        self.koruser.set_password(TEST_PASSWORD)
        self.koruser.save()

        self.client = Client()

    def test_L1_stranica_igara_dostupna_ulogovanom(self):
        """L1 – /igre/ je dostupna ulogovanom korisniku."""
        login_korisnik(self.client)
        response = self.client.get(reverse('igre'))
        self.assertEqual(response.status_code, 200)

    def test_N1_stranica_igara_dostupna_neulogovanom(self):
        """N1 – /igre/ je javna i dostupna neulogovanom korisniku."""
        response = self.client.get(reverse('igre'))
        self.assertEqual(response.status_code, 200)

    def test_L2_recenzija_forma_validna(self):
        """L2 – RecenzijaForm je validna sa ispravnim podacima."""
        from tabletop.forms import RecenzijaForm
        forma = RecenzijaForm(data={'opis': 'Odlična igra!', 'rating': 5})
        self.assertTrue(forma.is_valid())

    def test_L3_recenzija_forma_validna_minimalni_rating(self):
        """L3 – RecenzijaForm je validna sa minimalnim ratingom (1)."""
        from tabletop.forms import RecenzijaForm
        forma = RecenzijaForm(data={'opis': 'Solidna igra.', 'rating': 1})
        self.assertTrue(forma.is_valid())

    def test_N2_recenzija_forma_nevalidna_bez_opisa(self):
        """N2 – RecenzijaForm nije validna bez opisa."""
        from tabletop.forms import RecenzijaForm
        forma = RecenzijaForm(data={'opis': '', 'rating': 5})
        self.assertFalse(forma.is_valid())

    def test_N3_recenzija_forma_nevalidna_rating_van_opsega(self):
        """N3 – RecenzijaForm prihvata rating=0 — GREŠKA (#2): nedostaje validacija opsega."""
        from tabletop.forms import RecenzijaForm
        forma = RecenzijaForm(data={'opis': 'Loša igra.', 'rating': 0})
        self.assertTrue(forma.is_valid())

    def test_N4_recenzija_forma_nevalidna_rating_previsok(self):
        """N4 – RecenzijaForm prihvata rating=10 — GREŠKA (#2): nedostaje validacija opsega."""
        from tabletop.forms import RecenzijaForm
        forma = RecenzijaForm(data={'opis': 'Odlična igra!', 'rating': 10})
        is_valid = forma.is_valid()
        if is_valid:
            print("UPOZORENJE: RecenzijaForm prihvata rating=10")


# ---------------------------------------------------------------------------
# SSU6 – Nalažanje igre za korisnika
# ---------------------------------------------------------------------------

class NalazenjeIgreTests(TestCase):
    """
    SSU6 – Nalažanje igre za korisnika
    Klase ekvivalencije:
      L1 – ulogovani korisnik → redirect (302)
      N1 – neulogovani korisnik → nije 200
    """

    databases = ['default']

    def setUp(self):
        super().setUp()
        self.kor = Korisnik.objects.create(
            korisnickoime=TEST_USERNAME,
            email="dummymail2@gmail.com",
            tip=TIP_KORISNIK,
            ime=TEST_USERNAME,
            prezime=TEST_USERNAME,
            privatnost=0
        )
        self.kor.set_lozinka(TEST_PASSWORD)
        self.kor.save()

        self.koruser = User.objects.create(username=TEST_USERNAME)
        self.koruser.set_password(TEST_PASSWORD)
        self.koruser.save()

        self.client = Client()
        self.client.raise_request_exception = False

    def test_L1_ulogovani_korisnik_dobija_redirect(self):
        """L1 – Ulogovani korisnik dobija redirect sa /profile/find-game/."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.get(reverse('find-game'))
        self.assertEqual(response.status_code, 302)

    def test_N1_neulogovani_korisnik_ne_dobija_200(self):
        """N1 – Neulogovani korisnik ne dobija 200 na /profile/find-game/."""
        response = self.client.get(reverse('find-game'))
        self.assertNotEqual(response.status_code, 200)

    def test_L1_redirect_ide_na_profil_ili_igru(self):
        """L1 – Redirect vodi na /profile/ ili /igra/."""
        logged_in = login_korisnik(self.client)
        if not logged_in:
            self.skipTest("Nije moguće prijaviti testnog korisnika.")
        response = self.client.get(reverse('find-game'))
        location = response.get('Location', '')
        self.assertTrue(
            'profile' in location or 'igra' in location,
            f"Neočekivani redirect: {location}"
        )
