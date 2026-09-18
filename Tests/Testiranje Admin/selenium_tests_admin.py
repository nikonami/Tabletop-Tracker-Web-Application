#Maša Janković 0462/19
#selenium webdriver testovi za admin funkcionalnosti
#pokriva brisanje igre, brisanje korisnika i promenu info korisnika

import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
)

#kredencijali i podaci koji se koriste u testovima
BASE_URL = 'http://127.0.0.1:8000'

ADMIN_KORISNICKOIME = 'testadmin'
ADMIN_LOZINKA       = 'Admin123!'

NAZIV_IGRE_ZA_BRISANJE = 'TestIgraZaBrisanje'

KORISNICKOIME_ZA_BRISANJE = 'korisnik_brisanje'

#ime i prezime ovog korisnika, kako se prikazuju na kartici u /admin_users/
IME_ZA_BRISANJE = 'Selenium'
PREZIME_ZA_BRISANJE = 'TestBrisanje'

#ovom korisniku ce biti promenjena lozinka tokom testa
KORISNICKOIME_ZA_PROMENU = 'korisnik_promena'
NOVA_LOZINKA_ZA_PROMENU  = 'NovaSifra2026!'

#ime i prezime ovog korisnika, kako se prikazuju na kartici u /admin_users/
IME_ZA_PROMENU = 'Selenium'
PREZIME_ZA_PROMENU = 'TestPromena'


class AdminSeleniumBaznaKlasa(unittest.TestCase):
    #bazna klasa za sve selenium testove
    #pokrece chrome jednom po klasi i uloguje admina pre svakog testa

    @classmethod
    def setUpClass(cls):
        #pokrece chrome sa opcijama koje iskljucuju popupe
        opcije = Options()
        #ukloni komentar ispod za headless mod (bez prozora):
        #opcije.add_argument('--headless')
        opcije.add_argument('--no-sandbox')
        opcije.add_argument('--disable-dev-shm-usage')
        opcije.add_argument('--window-size=1280,900')
        #iskljucuje google password manager popup i upozorenje o probijenoj lozinci
        opcije.add_argument('--disable-save-password-bubble')
        opcije.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.password_manager_leak_detection': False,
            'profile.default_content_setting_values.notifications': 2,
        })
        opcije.add_experimental_option('excludeSwitches', ['enable-automation'])
        cls.driver = webdriver.Chrome(options=opcije)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        #zatvara browser kada su svi testovi u klasi gotovi
        cls.driver.quit()

    def setUp(self):
        #uloguje admina pre svakog testa
        self._uloguj_admina()

    def _uloguj_admina(self):
        #otvara stranicu za prijavu i uloguje admina
        #ceka na redirect koji se desava nakon uspesne prijave
        self.driver.get(f'{BASE_URL}/prijava/')
        try:
            self.wait.until(EC.presence_of_element_located((By.NAME, 'korisnicko_ime')))
        except TimeoutException:
            #sesija je vec aktivna pa /prijava/ redirektuje na drugu stranicu, prijava se preskace
            return
        self.driver.find_element(By.NAME, 'korisnicko_ime').clear()
        self.driver.find_element(By.NAME, 'korisnicko_ime').send_keys(ADMIN_KORISNICKOIME)
        self.driver.find_element(By.NAME, 'lozinka').clear()
        self.driver.find_element(By.NAME, 'lozinka').send_keys(ADMIN_LOZINKA)
        self._klikni(By.CSS_SELECTOR, 'button[type="submit"]')
        self.wait.until(EC.url_changes(f'{BASE_URL}/prijava/'))

    def _idi_na(self, putanja):
        #navigira na zadatu putanju
        self.driver.get(f'{BASE_URL}{putanja}')

    def _sacekaj_element(self, by, vrednost, timeout=10):
        #ceka da element postane vidljiv i vraca ga
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, vrednost))
        )

    def _element_postoji(self, by, vrednost):
        #vraca True ako element postoji u DOM-u, False inace
        try:
            self.driver.find_element(by, vrednost)
            return True
        except NoSuchElementException:
            return False

    def _klikni(self, by, vrednost, timeout=10):
        #ceka da element bude klikabilan, skroluje ga u centar ekrana i klikce
        #resava ElementClickInterceptedException kada fiksirani tab-bar prekriva element
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, vrednost))
        )
        self._klikni_element(element)

    def _klikni_element(self, element):
        #skroluje vec pronadjen element u centar ekrana i klikce
        #resava ElementClickInterceptedException kada fiksirani tab-bar prekriva element
        self.driver.execute_script('arguments[0].scrollIntoView({block: "center"});', element)
        try:
            element.click()
        except ElementClickInterceptedException:
            #rezervni klik preko JavaScript-a ako je element i dalje prekriven
            self.driver.execute_script('arguments[0].click();', element)


class TestPrijava(AdminSeleniumBaznaKlasa):
    #testira stranicu za prijavu

    def setUp(self):
        #ne ulogujemo se automatski jer testiramo samu prijavu
        #odjavljujemo prethodnu sesiju da /prijava/ ne bi redirektovala vec ulogovanog korisnika
        self._idi_na('/odjava/')

    def test_stranica_za_prijavu_se_ucitava(self):
        #stranica /prijava/ prikazuje formu sa oba polja i dugmetom
        self._idi_na('/prijava/')
        self.wait.until(EC.presence_of_element_located((By.NAME, 'korisnicko_ime')))
        self.assertTrue(self._element_postoji(By.NAME, 'korisnicko_ime'))
        self.assertTrue(self._element_postoji(By.NAME, 'lozinka'))
        self.assertTrue(self._element_postoji(By.CSS_SELECTOR, 'button[type="submit"]'))

    def test_uspesna_prijava_admina(self):
        #uspesna prijava preusmerava sa /prijava/ na drugu stranicu
        self._idi_na('/prijava/')
        self.wait.until(EC.presence_of_element_located((By.NAME, 'korisnicko_ime')))
        self.driver.find_element(By.NAME, 'korisnicko_ime').send_keys(ADMIN_KORISNICKOIME)
        self.driver.find_element(By.NAME, 'lozinka').send_keys(ADMIN_LOZINKA)
        self._klikni(By.CSS_SELECTOR, 'button[type="submit"]')
        self.wait.until(EC.url_changes(f'{BASE_URL}/prijava/'))
        self.assertNotIn('/prijava/', self.driver.current_url)

    def test_pogresna_lozinka_prikaz_greske(self):
        #pogresna lozinka ostavlja korisnika na /prijava/
        self._idi_na('/prijava/')
        self.wait.until(EC.presence_of_element_located((By.NAME, 'korisnicko_ime')))
        self.driver.find_element(By.NAME, 'korisnicko_ime').send_keys(ADMIN_KORISNICKOIME)
        self.driver.find_element(By.NAME, 'lozinka').send_keys('PogresnaLozinka999!')
        self._klikni(By.CSS_SELECTOR, 'button[type="submit"]')
        time.sleep(0.5)
        self.assertIn('/prijava/', self.driver.current_url)

    def test_prazna_polja_prikaz_greske(self):
        #prazna forma ostaje na /prijava/ bez preusmeravanja
        self._idi_na('/prijava/')
        self.wait.until(EC.presence_of_element_located((By.NAME, 'korisnicko_ime')))
        self._klikni(By.CSS_SELECTOR, 'button[type="submit"]')
        time.sleep(0.5)
        self.assertIn('/prijava/', self.driver.current_url)

    def test_nepostojeci_korisnik_prikaz_greske(self):
        #korisnicko ime koje ne postoji u bazi prikazuje gresku
        self._idi_na('/prijava/')
        self.wait.until(EC.presence_of_element_located((By.NAME, 'korisnicko_ime')))
        self.driver.find_element(By.NAME, 'korisnicko_ime').send_keys('korisnik_koji_ne_postoji_nikad')
        self.driver.find_element(By.NAME, 'lozinka').send_keys('NekaSifra1!')
        self._klikni(By.CSS_SELECTOR, 'button[type="submit"]')
        time.sleep(0.5)
        self.assertIn('/prijava/', self.driver.current_url)


class TestAdminPanel(AdminSeleniumBaznaKlasa):
    #testira navigaciju kroz admin panel
    #proverava dostupnost stranica i ispravnost tab bar linkova

    def test_admin_index_dostupan(self):
        #ulogovani admin moze da pristupi /admin_index/ i vidi kartice za korisnike i igre
        self._idi_na('/admin_index/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'section-title')))
        self.assertIn('admin_index', self.driver.current_url)
        self.assertTrue(self._element_postoji(By.LINK_TEXT, 'Upravljaj korisnicima'))
        self.assertTrue(self._element_postoji(By.LINK_TEXT, 'Upravljaj igrama'))

    def test_navigacija_do_liste_igara(self):
        #klik na 'Upravljaj igrama' vodi na /admin_games/
        self._idi_na('/admin_index/')
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Upravljaj igrama')))
        self._klikni(By.LINK_TEXT, 'Upravljaj igrama')
        self.wait.until(EC.url_contains('admin_games'))
        self.assertIn('admin_games', self.driver.current_url)

    def test_navigacija_do_liste_korisnika(self):
        #klik na 'Upravljaj korisnicima' vodi na /admin_users/
        self._idi_na('/admin_index/')
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Upravljaj korisnicima')))
        self._klikni(By.LINK_TEXT, 'Upravljaj korisnicima')
        self.wait.until(EC.url_contains('admin_users'))
        self.assertIn('admin_users', self.driver.current_url)

    def test_admin_games_lista_prikazana(self):
        #lista igara na /admin_games/ prikazuje item-list sa karticama igara
        self._idi_na('/admin_games/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'item-list')))
        self.assertIn('admin_games', self.driver.current_url)
        self.assertTrue(self._element_postoji(By.CLASS_NAME, 'item-list'))

    def test_admin_users_lista_prikazana(self):
        #lista korisnika na /admin_users/ prikazuje item-list sa karticama korisnika
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'item-list')))
        self.assertIn('admin_users', self.driver.current_url)
        self.assertTrue(self._element_postoji(By.CLASS_NAME, 'item-list'))

    def test_tab_bar_navigacija(self):
        #tab bar sadrzi linkove za Pocetna, Korisnici i Igre
        self._idi_na('/admin_games/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'tab-bar')))
        tab_bar = self.driver.find_element(By.CLASS_NAME, 'tab-bar')
        linkovi = tab_bar.find_elements(By.TAG_NAME, 'a')
        tekstovi = [link.text for link in linkovi]
        self.assertIn('Pocetna', tekstovi)
        self.assertIn('Korisnici', tekstovi)
        self.assertIn('Igre', tekstovi)

    def test_nelogovan_korisnik_ne_moze_admin_index(self):
        #nelogovan korisnik se preusmerava na stranicu za prijavu
        self._idi_na('/odjava/')
        time.sleep(0.5)
        self._idi_na('/admin_index/')
        time.sleep(0.5)
        self.assertTrue(
            '/prijava/' in self.driver.current_url or
            '/login/' in self.driver.current_url
        )


class TestBrisanjeIgreSelenium(AdminSeleniumBaznaKlasa):
    #testira scenario brisanja igre iz admin panela
    #koristi igru NAZIV_IGRE_ZA_BRISANJE definisanu na vrhu fajla

    def _nadji_igru_i_otvori_detalje(self, naziv):
        #na /admin_games/ pronalazi igru po nazivu i klikce Izaberi
        #vraca True ako je igra nadjena, False inace
        self._idi_na('/admin_games/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'item-list')))
        kartice = self.driver.find_elements(By.CLASS_NAME, 'card')
        for kartica in kartice:
            try:
                naslov = kartica.find_element(By.TAG_NAME, 'h3')
                if naslov.text.strip() == naziv:
                    self._klikni_element(kartica.find_element(By.CLASS_NAME, 'btn-select'))
                    self.wait.until(EC.url_contains('admin_games'))
                    return True
            except NoSuchElementException:
                continue
        return False

    def test_otvori_stranicu_detalja_igre(self):
        #klik na Izaberi vodi na stranicu detalja igre sa dugmadima Obrisi i Nazad
        self._idi_na('/admin_games/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.url_contains('admin_games/'))
        self.assertTrue(self._element_postoji(By.ID, 'btn-brisi'))
        self.assertTrue(self._element_postoji(By.LINK_TEXT, 'Nazad'))

    def test_klik_obrisi_otvara_confirm_box(self):
        #klik na Obrisi prikazuje confirm box sa inputom za naziv igre
        self._idi_na('/admin_games/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-brisi')))
        self._klikni(By.ID, 'btn-brisi')
        time.sleep(0.5)
        confirm_box = self._sacekaj_element(By.ID, 'delete-confirm-box')
        self.assertTrue(confirm_box.is_displayed())
        self.assertTrue(self._element_postoji(By.NAME, 'naziv_potvrda'))

    def test_otkazivanje_brisanja_igre(self):
        #klik na Odustani vraca na stranicu detalja bez brisanja igre
        self._idi_na('/admin_games/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-brisi')))
        self._klikni(By.ID, 'btn-brisi')
        time.sleep(0.5)
        self._klikni(By.LINK_TEXT, 'Odustani')
        time.sleep(0.5)
        self.assertIn('admin_games', self.driver.current_url)
        self.assertNotIn('confirm_delete=1', self.driver.current_url)

    def test_pogresno_ime_igre_prikaz_greske(self):
        #pogresno ime igre u confirm boxu prikazuje gresku u crvenom
        self._idi_na('/admin_games/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-brisi')))
        self._klikni(By.ID, 'btn-brisi')
        self._sacekaj_element(By.NAME, 'naziv_potvrda')
        self.driver.find_element(By.NAME, 'naziv_potvrda').send_keys('SIGURNO_POGRESNO_IME_12345')
        self._klikni(By.CSS_SELECTOR, '#delete-confirm-box button[type="submit"]')
        time.sleep(0.5)
        self.assertIn('admin_games', self.driver.current_url)
        greska_el = self.driver.find_elements(By.CSS_SELECTOR, 'p[style*="red"]')
        self.assertTrue(len(greska_el) > 0, 'Greska se ne prikazuje nakon pogresnog naziva igre')

    def test_uspesno_brisanje_igre(self):
        #tacan naziv igre u confirm boxu brise igru i prikazuje stranicu uspeha
        pronadjena = self._nadji_igru_i_otvori_detalje(NAZIV_IGRE_ZA_BRISANJE)
        if not pronadjena:
            self.skipTest(f'Igra "{NAZIV_IGRE_ZA_BRISANJE}" nije pronadjena u listi.')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-brisi')))
        self._klikni(By.ID, 'btn-brisi')
        self._sacekaj_element(By.NAME, 'naziv_potvrda')
        self.driver.find_element(By.NAME, 'naziv_potvrda').send_keys(NAZIV_IGRE_ZA_BRISANJE)
        self._klikni(By.CSS_SELECTOR, '#delete-confirm-box button[type="submit"]')
        self.wait.until(EC.url_contains('delete_success'))
        self.assertIn(NAZIV_IGRE_ZA_BRISANJE, self.driver.page_source)


class TestBrisanjeKorisnikaSelenium(AdminSeleniumBaznaKlasa):
    #testira scenario brisanja korisnika iz admin panela
    #koristi korisnika KORISNICKOIME_ZA_BRISANJE definisanog na vrhu fajla

    def _nadji_korisnika_i_otvori_detalje(self, ime, prezime):
        #na /admin_users/ pronalazi korisnika po imenu i prezimenu (to se prikazuje na kartici) i klikce Izaberi
        #vraca True ako je pronadjen, False inace
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'item-list')))
        kartice = self.driver.find_elements(By.CLASS_NAME, 'card')
        for kartica in kartice:
            if ime in kartica.text and prezime in kartica.text:
                self._klikni_element(kartica.find_element(By.CLASS_NAME, 'btn-select'))
                self.wait.until(EC.url_contains('admin_users/user'))
                return True
        return False

    def test_otvori_stranicu_detalja_korisnika(self):
        #klik na Izaberi vodi na stranicu detalja korisnika sa dugmadima Obrisi, Izmeni i Nazad
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.url_contains('admin_users/user'))
        self.assertTrue(self._element_postoji(By.ID, 'btn-brisi'))
        self.assertTrue(self._element_postoji(By.ID, 'btn-izmeni'))
        self.assertTrue(self._element_postoji(By.LINK_TEXT, 'Nazad'))

    def test_klik_obrisi_otvara_confirm_box(self):
        #klik na Obrisi prikazuje confirm box sa inputom za korisnicko ime
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-brisi')))
        self._klikni(By.ID, 'btn-brisi')
        time.sleep(0.5)
        confirm_box = self._sacekaj_element(By.ID, 'delete-confirm-box')
        self.assertTrue(confirm_box.is_displayed())
        self.assertTrue(self._element_postoji(By.NAME, 'username_potvrda'))

    def test_otkazivanje_brisanja_korisnika(self):
        #klik na Odustani vraca na stranicu detalja bez brisanja korisnika
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-brisi')))
        self._klikni(By.ID, 'btn-brisi')
        time.sleep(0.5)
        self._klikni(By.LINK_TEXT, 'Odustani')
        time.sleep(0.5)
        self.assertIn('admin_users/user', self.driver.current_url)
        self.assertNotIn('confirm_delete=1', self.driver.current_url)

    def test_pogresno_korisnicko_ime_prikaz_greske(self):
        #pogresno korisnicko ime u confirm boxu prikazuje gresku u crvenom
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-brisi')))
        self._klikni(By.ID, 'btn-brisi')
        self._sacekaj_element(By.NAME, 'username_potvrda')
        self.driver.find_element(By.NAME, 'username_potvrda').send_keys('POGRESNO_IME_SIGURNO_12345')
        self._klikni(By.CSS_SELECTOR, '#delete-confirm-box button[type="submit"]')
        time.sleep(0.5)
        self.assertIn('admin_users/user', self.driver.current_url)
        greska_el = self.driver.find_elements(By.CSS_SELECTOR, 'p[style*="red"]')
        self.assertTrue(len(greska_el) > 0, 'Greska se ne prikazuje nakon pogresnog korisnickog imena')

    def test_uspesno_brisanje_korisnika(self):
        #tacno korisnicko ime u confirm boxu brise korisnika i prikazuje stranicu uspeha
        pronadjen = self._nadji_korisnika_i_otvori_detalje(IME_ZA_BRISANJE, PREZIME_ZA_BRISANJE)
        if not pronadjen:
            self.skipTest(f'Korisnik "{IME_ZA_BRISANJE} {PREZIME_ZA_BRISANJE}" nije pronadjen u listi.')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-brisi')))
        self._klikni(By.ID, 'btn-brisi')
        self._sacekaj_element(By.NAME, 'username_potvrda')
        self.driver.find_element(By.NAME, 'username_potvrda').send_keys(KORISNICKOIME_ZA_BRISANJE)
        self._klikni(By.CSS_SELECTOR, '#delete-confirm-box button[type="submit"]')
        self.wait.until(EC.url_contains('delete_success'))
        self.assertIn('delete_success', self.driver.current_url)


class TestPromenaInfoKorisnikaSelenium(AdminSeleniumBaznaKlasa):
    #testira scenario promene korisnickih informacija iz admin panela
    #koristi korisnika KORISNICKOIME_ZA_PROMENU definisanog na vrhu fajla

    def _otvori_korisnika(self, ime, prezime):
        #pronalazi korisnika u listi po imenu i prezimenu (to se prikazuje na kartici) i otvara mu stranicu detalja
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'item-list')))
        kartice = self.driver.find_elements(By.CLASS_NAME, 'card')
        for kartica in kartice:
            if ime in kartica.text and prezime in kartica.text:
                self._klikni_element(kartica.find_element(By.CLASS_NAME, 'btn-select'))
                self.wait.until(EC.url_contains('admin_users/user'))
                return True
        return False

    def test_klik_izmeni_otvara_change_formu(self):
        #klik na Izmeni prikazuje change box sa poljima za korisnicko ime i lozinku
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-izmeni')))
        self._klikni(By.ID, 'btn-izmeni')
        time.sleep(0.5)
        change_box = self._sacekaj_element(By.ID, 'change-box')
        self.assertTrue(change_box.is_displayed())
        self.assertTrue(self._element_postoji(By.NAME, 'korisnickoime'))
        self.assertTrue(self._element_postoji(By.NAME, 'lozinka'))

    def test_otkazivanje_izmene(self):
        #klik na Odustani vraca na stranicu detalja bez promene podataka
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-izmeni')))
        self._klikni(By.ID, 'btn-izmeni')
        time.sleep(0.5)
        self._klikni(By.LINK_TEXT, 'Odustani')
        time.sleep(0.5)
        self.assertIn('admin_users/user', self.driver.current_url)
        self.assertNotIn('change=1', self.driver.current_url)

    def test_prazna_polja_daju_gresku(self):
        #prazno korisnicko ime i lozinka daju gresku o obaveznim poljima
        self._idi_na('/admin_users/')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-select')))
        self._klikni(By.CLASS_NAME, 'btn-select')
        self.wait.until(EC.presence_of_element_located((By.ID, 'btn-izmeni')))
        self._klikni(By.ID, 'btn-izmeni')
        self._sacekaj_element(By.ID, 'change-box')
        self.driver.find_element(By.NAME, 'korisnickoime').clear()
        self.driver.find_element(By.NAME, 'lozinka').clear()
        self._klikni(By.CSS_SELECTOR, '#change-box button[type="submit"]')
        time.sleep(0.5)
        self.assertIn('admin_users/user', self.driver.current_url)

    def test_nevalidna_lozinka_prikaz_greske(self):
        #lozinka koja ne ispunjava uslove prikazuje gresku u crvenom
        pronadjen = self._otvori_korisnika(IME_ZA_PROMENU, PREZIME_ZA_PROMENU)
        if not pronadjen:
            self.skipTest(f'Korisnik "{IME_ZA_PROMENU} {PREZIME_ZA_PROMENU}" nije pronadjen.')
        self._klikni(By.ID, 'btn-izmeni')
        self._sacekaj_element(By.ID, 'change-box')
        lozinka_input = self.driver.find_element(By.NAME, 'lozinka')
        lozinka_input.clear()
        lozinka_input.send_keys('kratka')
        self._klikni(By.CSS_SELECTOR, '#change-box button[type="submit"]')
        time.sleep(0.5)
        self.assertIn('admin_users/user', self.driver.current_url)
        greska_el = self.driver.find_elements(By.CSS_SELECTOR, 'p[style*="red"]')
        self.assertTrue(len(greska_el) > 0, 'Greska za nevalidnu lozinku se ne prikazuje')

    def test_uspesna_promena_lozinke(self):
        #nova validna lozinka se cuva i prikazuje se stranica uspeha
        pronadjen = self._otvori_korisnika(IME_ZA_PROMENU, PREZIME_ZA_PROMENU)
        if not pronadjen:
            self.skipTest(f'Korisnik "{IME_ZA_PROMENU} {PREZIME_ZA_PROMENU}" nije pronadjen.')
        self._klikni(By.ID, 'btn-izmeni')
        self._sacekaj_element(By.ID, 'change-box')
        lozinka_input = self.driver.find_element(By.NAME, 'lozinka')
        lozinka_input.clear()
        lozinka_input.send_keys(NOVA_LOZINKA_ZA_PROMENU)
        self._klikni(By.CSS_SELECTOR, '#change-box button[type="submit"]')
        self.wait.until(EC.url_contains('change_success'))
        self.assertIn('change_success', self.driver.current_url)

    def test_isti_podaci_daju_gresku(self):
        #isti podaci kao sto korisnik vec ima daju gresku
        pronadjen = self._otvori_korisnika(IME_ZA_PROMENU, PREZIME_ZA_PROMENU)
        if not pronadjen:
            self.skipTest(f'Korisnik "{IME_ZA_PROMENU} {PREZIME_ZA_PROMENU}" nije pronadjen.')
        self._klikni(By.ID, 'btn-izmeni')
        self._sacekaj_element(By.ID, 'change-box')
        #korisnicko ime ostaje isto, saljemo trenutnu lozinku (koja je promenjena u prethodnom testu)
        lozinka_input = self.driver.find_element(By.NAME, 'lozinka')
        lozinka_input.clear()
        lozinka_input.send_keys(NOVA_LOZINKA_ZA_PROMENU)
        self._klikni(By.CSS_SELECTOR, '#change-box button[type="submit"]')
        time.sleep(0.5)
        self.assertIn('admin_users/user', self.driver.current_url)


if __name__ == '__main__':
    #verbose=2 prikazuje ime svakog testa i rezultat
    unittest.main(verbosity=2)
