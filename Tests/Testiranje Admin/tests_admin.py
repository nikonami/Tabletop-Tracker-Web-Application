# jedinicni testovi za funkcionalnosti admina
# pokriva: brisanje igre, brisanje korisnika, promena info korisnika
# Masa Jankovic 0462/19

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import datetime
from tabletop.models import Korisnik, Igra

# pomocne funkcije za pravljenje test podataka

def napravi_admina(korisnickoime='testadmin', lozinka='Admin123!'):
    #kreira admina i u Korisnik tabeli i u Django User tabeli
    import hashlib
    lozinka_hash = hashlib.sha1(lozinka.encode('utf-8')).hexdigest()
    korisnik = Korisnik.objects.create(
        korisnickoime=korisnickoime,
        lozinka=lozinka_hash,
        email=f'{korisnickoime}@test.com',
        tip=Korisnik.TIP_ADMINISTRATOR,
        ime='Test',
        prezime='Admin',
        privatnost=0,
        obrisan=0,
    )
    django_user = User.objects.create_user(username=korisnickoime, password=lozinka)
    return korisnik, django_user, lozinka


def napravi_korisnika(korisnickoime='testkorisnik', lozinka='Korisnik123!', tip=Korisnik.TIP_KORISNIK):
    #kreira obicnog korisnika i u Korisnik tabeli i u Django User tabeli
    import hashlib
    lozinka_hash = hashlib.sha1(lozinka.encode('utf-8')).hexdigest()
    korisnik = Korisnik.objects.create(
        korisnickoime=korisnickoime,
        lozinka=lozinka_hash,
        email=f'{korisnickoime}@test.com',
        tip=tip,
        ime='Test',
        prezime='Korisnik',
        privatnost=0,
        obrisan=0,
    )
    django_user = User.objects.create_user(username=korisnickoime, password=lozinka)
    return korisnik, django_user, lozinka


def napravi_igru(naziv='Test Igra', obrisan=0):
    #kreira igru u bazi
    igra = Igra.objects.create(
        naziv=naziv,
        godinaproizvodnje=datetime(2020, 1, 1),
        minigraca=2,
        maxigraca=4,
        opis='Opis test igre',
        slikaurl='http://example.com/slika.jpg',
        videotutorialurl='http://example.com/video.mp4',
        obrisan=obrisan,
    )
    return igra


def uloguj_admina(client, korisnik_obj, lozinka):
    #loguje admina kroz Django auth sistem i postavlja sve session vrednosti koje @admin_required dekorator ocekuje
    #takodje postavlja request.trenutni_korisnik koji neke view funkcije koriste

    client.login(username=korisnik_obj.korisnickoime, password=lozinka)
    session = client.session
    session['idkor'] = korisnik_obj.idkor
    session['tip'] = korisnik_obj.tip          # TIP_ADMINISTRATOR = 3
    session['korisnickoime'] = korisnik_obj.korisnickoime
    session['ime'] = korisnik_obj.ime
    session.save()


# TESTOVI ZA BRISANJE IGRE (SSU_admin_brisanje_igre)

class AdminBrisanjeIgreTest(TestCase):
    #testira scenarije iz SSU_admin_brisanje_igre:
    #uspesno brisanje igre
    #pogresno ime igre
    #otkazivanje operacije

    def setUp(self):
        #priprema podataka pre svakog testa u ovoj klasi
        self.client = Client()
        self.admin, self.django_admin, self.lozinka = napravi_admina()
        self.igra = napravi_igru(naziv='Catan')
        uloguj_admina(self.client, self.admin, self.lozinka)

    # model testovi

    def test_igra_postoji_u_bazi(self):
        #nova igra treba da postoji i da nije oznacena kao obrisana
        igra = Igra.objects.get(idigre=self.igra.idigre)
        self.assertIn(igra.obrisan, [0, None])

    def test_soft_delete_igre_postavlja_obrisan_na_1(self):
        #soft-delete igre treba da postavi polje obrisan = 1
        #igra se ne brise iz baze
        self.igra.obrisan = 1
        self.igra.save(update_fields=['obrisan'])

        igra_iz_baze = Igra.objects.get(idigre=self.igra.idigre)
        self.assertEqual(igra_iz_baze.obrisan, 1)

    def test_obrisana_igra_nije_u_aktivnom_queryetu(self):
        #igra sa obrisan = 1 ne sme da se pojavi u listi aktivnih igara
        from django.db.models import Q
        self.igra.obrisan = 1
        self.igra.save(update_fields=['obrisan'])

        aktivne = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0))
        self.assertNotIn(self.igra, aktivne)

    # view testovi

    def test_admin_game_detalji_get(self):
        #GET na stranicu detalja igre vraca 200 i prikazuje naziv igre
        url = reverse('admin_game_detalji', args=[self.igra.idigre])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.igra.naziv)

    def test_prikaz_confirm_delete_boxa(self):
        #dodavanje ?confirm_delete=1 u URL treba da prikaze polje za potvrdu
        url = reverse('admin_game_detalji', args=[self.igra.idigre])
        response = self.client.get(url + '?confirm_delete=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_delete_confirm'])

    def test_uspesno_brisanje_igre(self):
        #SSU: Administrator uspesno brise igru.
        #POST sa tacnim nazivom igre -> redirect na stranicu uspeha
        #igra je oznacena kao obrisana u bazi

        url = reverse('admin_game_detalji', args=[self.igra.idigre])
        response = self.client.post(url, {'naziv_potvrda': 'Catan'})

        #view treba da redirectuje ka delete_success stranici
        self.assertEqual(response.status_code, 302)

        #igra u bazi mora imati obrisan = 1
        self.igra.refresh_from_db()
        self.assertEqual(self.igra.obrisan, 1)

    def test_pogresno_ime_igre_daje_gresku(self):
        #SSU: Administrator unosi pogresno ime igre
        #treba da ostane na stranici, prikaze gresku, igra NE sme biti obrisana

        url = reverse('admin_game_detalji', args=[self.igra.idigre])
        response = self.client.post(url, {'naziv_potvrda': 'PogresnoIme'})

        #ostaje na istoj stranici (nema redirecta)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_delete_confirm'])
        self.assertIsNotNone(response.context['delete_error'])

        #igra ostaje aktivna
        self.igra.refresh_from_db()
        self.assertIn(self.igra.obrisan, [0, None])

    def test_prazan_naziv_ne_brise_igru(self):
        #prazan string kao naziv ne sme obrisati igru
        url = reverse('admin_game_detalji', args=[self.igra.idigre])
        self.client.post(url, {'naziv_potvrda': ''})

        self.igra.refresh_from_db()
        self.assertIn(self.igra.obrisan, [0, None])

    def test_brisanje_case_sensitive(self):
        #SSU: Naziv igre je case-sensitive
        #igra ne sme biti obrisana
        url = reverse('admin_game_detalji', args=[self.igra.idigre])
        self.client.post(url, {'naziv_potvrda': 'catan'})

        self.igra.refresh_from_db()
        self.assertIn(self.igra.obrisan, [0, None])

    def test_delete_success_stranica_prikazuje_naziv(self):
        #nakon uspesnog brisanja, stranica uspeha treba da prikaze naziv igre
        #session guard (admin_game_delete_success_id) mora biti postavljen

        session = self.client.session
        session['admin_game_delete_success_id'] = self.igra.idigre
        session.save()

        url = reverse('admin_game_delete_success', args=[self.igra.idigre])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.igra.naziv)

    def test_delete_success_bez_sesije_redirectuje(self):
        #direktan pristup delete_success URL-u bez session guard-a
        #treba da redirectuje (sprecava random pristup URL-u)

        url = reverse('admin_game_delete_success', args=[self.igra.idigre])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_nema_pristupa_bez_logovanja(self):
        #nelogovan korisnik ne sme pristupiti admin stranicama

        self.client.logout()
        url = reverse('admin_game_detalji', args=[self.igra.idigre])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_obican_korisnik_nema_admin_pristup(self):
        #obican korisnik (tip = 1) ne sme pristupiti admin stranicama
        korisnik, _, lozinka = napravi_korisnika('obican', 'Obican123!')
        self.client.logout()
        uloguj_admina(self.client, korisnik, lozinka)

        url = reverse('admin_game_detalji', args=[self.igra.idigre])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)


# TESTOVI ZA BRISANJE KORISNIKA (SSU_admin_brisanje_korisnika)

class AdminBrisanjeKorisnikaTest(TestCase):
    #testira scenarije iz SSU_admin_brisanje_korisnika:
    #spesno brisanje korisnika
    #pogresno korisnicko ime
    #otkazivanje operacije

    def setUp(self):
        self.client = Client()
        self.admin, self.django_admin, self.admin_lozinka = napravi_admina()
        self.korisnik, self.django_k, self.k_lozinka = napravi_korisnika(
            korisnickoime='zrtva_brisanja', lozinka='Zrtva123!'
        )
        uloguj_admina(self.client, self.admin, self.admin_lozinka)

    # model testovi

    def test_korisnik_postoji_u_bazi(self):
        #novokreirani korisnik treba da postoji sa obrisan = 0

        k = Korisnik.objects.get(idkor=self.korisnik.idkor)
        self.assertEqual(k.obrisan, 0)

    def test_soft_delete_korisnika_postavlja_obrisan_na_1(self):
        #soft-delete postavlja obrisan = 1, korisnik fizicki ostaje u bazi

        self.korisnik.obrisan = 1
        self.korisnik.save(update_fields=['obrisan'])

        k = Korisnik.objects.get(idkor=self.korisnik.idkor)
        self.assertEqual(k.obrisan, 1)

    def test_obrisani_korisnik_nije_u_aktivnom_queryetu(self):
        #korisnik sa obrisan = 1 ne sme biti u filtriranom queryetu aktivnih

        self.korisnik.obrisan = 1
        self.korisnik.save(update_fields=['obrisan'])

        aktivni = Korisnik.objects.filter(obrisan=0)
        self.assertNotIn(self.korisnik, aktivni)

    # view testovi

    def test_admin_user_detalji_get(self):
        #GET na stranicu detalja korisnika vraca 200 i prikazuje korisnicko ime

        url = reverse('admin_user_detalji', args=[self.korisnik.idkor])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.korisnik.korisnickoime)

    def test_prikaz_confirm_delete_boxa(self):
        #?confirm_delete = 1 treba da prikaze polje za potvrdu brisanja

        url = reverse('admin_user_detalji', args=[self.korisnik.idkor])
        response = self.client.get(url + '?confirm_delete=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_delete_confirm'])

    def test_uspesno_brisanje_korisnika(self):
        #SSU: Administrator uspesno brise korisnika
        #POST sa tacnim korisnickim imenom -> redirect, korisnik ima obrisan = 1

        url = reverse('admin_user_detalji', args=[self.korisnik.idkor])
        response = self.client.post(url, {
            'action': 'delete',
            'username_potvrda': 'zrtva_brisanja'
        })

        self.assertEqual(response.status_code, 302)

        self.korisnik.refresh_from_db()
        self.assertEqual(self.korisnik.obrisan, 1)

    def test_uspesno_brisanje_brise_i_iz_django_user(self):
        #nakon brisanja, korisnik mora biti obrisan i iz Django User tabele

        url = reverse('admin_user_detalji', args=[self.korisnik.idkor])
        self.client.post(url, {
            'action': 'delete',
            'username_potvrda': 'zrtva_brisanja'
        })

        postoji_u_django = User.objects.filter(username='zrtva_brisanja').exists()
        self.assertFalse(postoji_u_django)

    def test_pogresno_korisnicko_ime_daje_gresku(self):
        #SSU: Administrator unosi pogresno korisnicko ime
        #korisnik NE sme biti obrisan, prikaze se greska
        url = reverse('admin_user_detalji', args=[self.korisnik.idkor])
        response = self.client.post(url, {
            'action': 'delete',
            'username_potvrda': 'POGRESNO_IME'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['delete_error'])

        self.korisnik.refresh_from_db()
        self.assertEqual(self.korisnik.obrisan, 0)

    def test_brisanje_case_sensitive(self):
        #potvrda korisnickog imena je case-sensitive
        url = reverse('admin_user_detalji', args=[self.korisnik.idkor])
        self.client.post(url, {
            'action': 'delete',
            'username_potvrda': 'ZRTVA_BRISANJA'  # pogresna velicina slova
        })

        self.korisnik.refresh_from_db()
        self.assertEqual(self.korisnik.obrisan, 0)

    def test_admin_ne_moze_da_obrise_admina(self):
        #admin ne sme moci da pristupi stranici drugog admina
        #view treba da redirectuje na admin_index

        admin2, _, _ = napravi_admina(korisnickoime='admin2', lozinka='Admin2123!')

        url = reverse('admin_user_detalji', args=[admin2.idkor])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_delete_success_stranica(self):
        #nakon uspesnog brisanja, stranica uspeha se prikazuje uz session guard
        session = self.client.session
        session['admin_user_delete_success_id'] = self.korisnik.idkor
        session.save()

        url = reverse('admin_user_delete_success', args=[self.korisnik.idkor])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_success_bez_sesije_redirectuje(self):
        #direktan pristup delete_success bez session guard-a -> redirect
        url = reverse('admin_user_delete_success', args=[self.korisnik.idkor])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


# TESTOVI ZA PROMENU KORISNICKIH INFORMACIJA (SSU_admin_promena_info_korisnika)

class AdminPromenaInfoKorisnikaTest(TestCase):
    #testira scenarije iz SSU_admin_promena_info_korisnika:
    #uspesna promena korisnickog imena i lozinke
    #uspesna promena samo lozinke
    #vec postojece korisnicko ime
    #nevalidna lozinka
    #isti podaci kao postojeci
    #prazna polja

    def setUp(self):
        self.client = Client()
        self.admin, self.django_admin, self.admin_lozinka = napravi_admina()
        self.stara_lozinka = 'Stara123!'
        self.korisnik, self.django_k, _ = napravi_korisnika(
            korisnickoime='menjani_korisnik', lozinka=self.stara_lozinka
        )
        uloguj_admina(self.client, self.admin, self.admin_lozinka)

    def _post_change(self, korisnickoime, lozinka):
        #salje POST za promenu podataka korisnika
        url = reverse('admin_user_detalji', args=[self.korisnik.idkor])
        return self.client.post(url, {
            'action': 'change',
            'korisnickoime': korisnickoime,
            'lozinka': lozinka,
        })

    # model testovi

    def test_promena_korisnickog_imena_u_modelu(self):
        #direktna izmena korisnickog imena menja vrednost u bazi

        self.korisnik.korisnickoime = 'novo_ime'
        self.korisnik.save(update_fields=['korisnickoime'])

        k = Korisnik.objects.get(idkor = self.korisnik.idkor)
        self.assertEqual(k.korisnickoime, 'novo_ime')

    def test_promena_lozinke_cuva_hash(self):
        #promena lozinke cuva SHA1 hash, ne plaintext

        import hashlib
        nova_hash = hashlib.sha1('NovaLozinka1!'.encode('utf-8')).hexdigest()
        self.korisnik.lozinka = nova_hash
        self.korisnik.save(update_fields=['lozinka'])

        k = Korisnik.objects.get(idkor=self.korisnik.idkor)
        self.assertEqual(k.lozinka, nova_hash)
        # lozinka nije plaintext
        self.assertNotEqual(k.lozinka, 'NovaLozinka1!')

    def test_datum_izmene_se_azurira_nakon_promene(self):
        #datumizmene treba da se postavi na trenutno vreme pri promeni
        from django.utils import timezone
        pre_izmene = timezone.now()

        self.korisnik.datumizmene = timezone.now()
        self.korisnik.save(update_fields=['datumizmene'])

        k = Korisnik.objects.get(idkor=self.korisnik.idkor)
        self.assertIsNotNone(k.datumizmene)
        self.assertGreaterEqual(k.datumizmene, pre_izmene)

    # view testovi

    def test_prikaz_change_forma(self):
        #?change=1 u URL treba da prikaze formu za izmenu
        url = reverse('admin_user_detalji', args=[self.korisnik.idkor])
        response = self.client.get(url + '?change=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_change_form'])

    def test_uspesna_promena_korisnickog_imena_i_lozinke(self):
        #SSU: Administrator uspesno menja i korisnicko ime i lozinku
        #redirect na change_success, novo korisnicko ime sacuvano u bazi
        
        response = self._post_change('novo_ime_korisnika', 'NovaLozinka1!')

        self.assertEqual(response.status_code, 302)

        self.korisnik.refresh_from_db()
        self.assertEqual(self.korisnik.korisnickoime, 'novo_ime_korisnika')

    def test_promena_azurira_i_django_user_tabelu(self):
        #nakon promene korisnickog imena, Django User tabela mora biti azurirana
        #staro ime ne sme postojati, novo mora

        self._post_change('novo_django_ime', 'NovaLozinka1!')

        self.assertTrue(User.objects.filter(username='novo_django_ime').exists())
        self.assertFalse(User.objects.filter(username='menjani_korisnik').exists())

    def test_uspesna_promena_samo_lozinke(self):
        #SSU: Administrator uspesno menja samo lozinku
        #nova lozinka mora biti hesirano sacuvana

        import hashlib
        response = self._post_change('menjani_korisnik', 'SamoNovaLozinka1!')

        self.assertEqual(response.status_code, 302)

        ocekivana_hash = hashlib.sha1('SamoNovaLozinka1!'.encode('utf-8')).hexdigest()
        self.korisnik.refresh_from_db()
        self.assertEqual(self.korisnik.lozinka, ocekivana_hash)

    def test_vec_postojece_korisnicko_ime_daje_gresku(self):
        #SSU: Administrator unosi vec postojece korisnicko ime
        #prikaze se greska, podaci ostaju nepromenjeni

        napravi_korisnika('zauzeto_ime', 'Zauzeto123!')

        response = self._post_change('zauzeto_ime', 'NovaLozinka1!')

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['change_error'])

        # korisnicko ime ostaje nepromenjeno
        self.korisnik.refresh_from_db()
        self.assertEqual(self.korisnik.korisnickoime, 'menjani_korisnik')

    def test_nevalidna_lozinka_prekratka(self):
        #SSU: Nevalidna lozinka (manje od 8 znakova)

        response = self._post_change('menjani_korisnik', 'Kratk1!')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['change_error'])

    def test_nevalidna_lozinka_bez_specijalnog_znaka(self):
        #SSU: Lozinka bez specijalnog znaka
            
        response = self._post_change('menjani_korisnik', 'BezSpecijala1')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['change_error'])

    def test_nevalidna_lozinka_bez_velikog_slova(self):
        #lozinka bez velikog slova treba da bude odbijena

        response = self._post_change('menjani_korisnik', 'bezvelikog1!')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['change_error'])

    def test_isti_podaci_kao_postojeci_daju_gresku(self):
        #SSU: Administrator unosi iste podatke kao sto korisnik vec ima
        #saljemo isto korisnicko ime i istu lozinku (plaintext, view ce je hesirati i uporediti)

        response = self._post_change('menjani_korisnik', self.stara_lozinka)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['change_error'])

    def test_prazno_korisnicko_ime_daje_gresku(self):
        #prazno korisnicko ime mora biti odbijena

        response = self._post_change('', 'NovaLozinka1!')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['change_error'])

    def test_prazna_lozinka_daje_gresku(self):
        #prazna lozinka mora biti odbijena

        response = self._post_change('menjani_korisnik', '')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['change_error'])

    def test_korisnicko_ime_predugacko(self):
        #korisnicko ime duze od 30 znakova mora biti odbijena

        predugacko = 'a' * 31
        response = self._post_change(predugacko, 'NovaLozinka1!')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['change_error'])

    def test_change_success_stranica(self):
        #nakon uspesne promene, change_success stranica se prikazuje
        session = self.client.session
        session['admin_user_change_success_id'] = self.korisnik.idkor
        session.save()

        url = reverse('admin_user_change_success', args=[self.korisnik.idkor])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.korisnik.korisnickoime)

    def test_change_success_bez_sesije_redirectuje(self):
        #direktan pristup change_success URL-u bez session guard-a -> redirect
        url = reverse('admin_user_change_success', args=[self.korisnik.idkor])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


# ===========================================================================
# TESTOVI ZA ADMIN LISTU (admin_games i admin_users)
# ===========================================================================

class AdminListeTest(TestCase):
    #testira prikaz lista igara i korisnika u admin panelu

    def setUp(self):
        self.client = Client()
        self.admin, _, self.lozinka = napravi_admina()
        self.igra = napravi_igru(naziv='Wingspan')
        self.korisnik, _, _ = napravi_korisnika('lista_korisnik', 'Lista123!')
        uloguj_admina(self.client, self.admin, self.lozinka)

    def test_admin_index_prikaz(self):
        #admin index stranica vraca 200 i prosledjuje broj igara i korisnika
        url = reverse('admin_index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('broj_igara', response.context)
        self.assertIn('broj_korisnika', response.context)

    def test_admin_index_broji_aktivne_igre(self):
        #broj igara na index-u ne sme ukljucivati obrisane igre
        igra_obrisana = napravi_igru(naziv='ObrisanaIgra', obrisan=1)

        url = reverse('admin_index')
        response = self.client.get(url)
        #samo Wingspan je aktivna, ObrisanaIgra nije
        self.assertEqual(response.context['broj_igara'], 1)

    def test_admin_games_prikazuje_aktivne_igre(self):
        #lista igara vraca 200 i sadrzi aktivnu igru
        url = reverse('admin_games')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wingspan')

    def test_admin_games_ne_prikazuje_obrisane(self):
        #obrisane igre ne smeju biti u context['igre']
        self.igra.obrisan = 1
        self.igra.save(update_fields=['obrisan'])

        url = reverse('admin_games')
        response = self.client.get(url)
        self.assertNotIn(self.igra, response.context['igre'])

    def test_admin_users_prikazuje_korisnike(self):
        #lista korisnika vraca 200 i sadrzi kreiranog korisnika
        url = reverse('admin_users')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.korisnik, response.context['korisnici'])

    def test_admin_users_ne_prikazuje_admina(self):
        #admin se ne sme pojaviti u listi korisnika
        url = reverse('admin_users')
        response = self.client.get(url)
        for k in response.context['korisnici']:
            self.assertNotEqual(k.tip, Korisnik.TIP_ADMINISTRATOR)

    def test_admin_users_ne_prikazuje_obrisane(self):
        #obrisani korisnici (obrisan = 1) ne smeju biti u listi
        self.korisnik.obrisan = 1
        self.korisnik.save(update_fields=['obrisan'])

        url = reverse('admin_users')
        response = self.client.get(url)
        self.assertNotIn(self.korisnik, response.context['korisnici'])
