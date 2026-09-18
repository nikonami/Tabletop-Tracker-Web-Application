#Darko Omerovic 2017/0653
#Testiranje gosta,registacije i logina za sve tipove korisnika(korisnik,moderator,admin)

from django.test import TestCase,Client

from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .models import *
from .views import *


class GostFunckionalnostiTestCase(TestCase):
    def setUp(self):
        super().setUp()
        igra = Igra.objects.create(
            naziv="Gejm",
            godinaproizvodnje="2022-01-01",
            minigraca=1,
            maxigraca=3,
            opis="Neka Igra.",
            slikaurl="https://www.google.com/",
            videotutorialurl="https://www.youtube.com/",
            zanr="komplikovana igra"
        )
        igra.save()

        self.client = Client()


    def test_gost_uspesan_pristup_pocetnoj(self):
        response = self.client.get('/', follow=True)

        # Proverava da je / preusmerio na /igre/
        self.assertRedirects(response, 'igre/')

        # Proverava da je konačna stranica uspešno otvorena
        self.assertEqual(response.status_code, 200)

        # Proverava da je naziv kreirane igre prikazan na stranici
        self.assertContains(response, "Gejm")

    def test_gost_neuspesan_pristup(self):
        response = self.client.get(reverse("admin_users"))
        
        #Provera da je preusmeren
        self.assertEqual(response.status_code, 302)

        #Porvera da je preusmeren na pravu lokaciju
        self.assertTrue(response.url.startswith(
            "http://127.0.0.1:8000/prijava/"
        ))

    def test_gost_uspesan_pristup_prijavi(self):
        response = self.client.get(reverse("igre"))

        # Provera da Login link postoji u meniju
        self.assertContains(
            response,
            f'href="{reverse("prijava")}"'
        )

        # Provera rute za prijavu
        response = self.client.get(reverse("prijava"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/prijava/")

    def test_gost_uspesan_pristup_registraciji(self):
        response = self.client.get(reverse("prijava"))

        # Provera da Registruj se link postoji
        self.assertContains(
            response,
            f'href="{reverse("registracija")}"'
        )

        # Provera rute za registraciju
        response = self.client.get(reverse("registracija"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/registracija/")



class AutentifikacijaTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.igra = Igra.objects.create(
            naziv="Gejm",
            godinaproizvodnje="2022-01-01",
            minigraca=1,
            maxigraca=3,
            opis="Neka Igra.",
            slikaurl="https://www.google.com/",
            videotutorialurl="https://www.youtube.com/",
            zanr="komplikovana igra"
        )

        admin = Korisnik.objects.create(
            korisnickoime="adminuser",
            email="admin@gmail.com",
            tip=TIP_ADMIN,
            ime="Admin",
            prezime="Adminic",
            privatnost=0,
            obrisan=0
        )
        admin.set_lozinka("Admin123!")
        admin.save()

        adminuser = User.objects.create(
            username="adminuser"
        )
        adminuser.set_password("Admin123!")
        adminuser.save()


        mod = Korisnik.objects.create(
            korisnickoime="moduser",
            email="mailmail@gmail.com",
            tip=TIP_MODERATOR,
            ime="Djole",
            prezime="Djokovic",
            privatnost=0
        )
        mod.set_lozinka("Djole123!")
        mod.save()

        moduser = User.objects.create(
            username="moduser",
        )
        moduser.set_password("Djole123!")
        moduser.save()

        kor = Korisnik.objects.create(
            korisnickoime="reguser",
            email="mail@gmail.com",
            tip=TIP_KORISNIK,
            ime="Petar",
            prezime="Petrovic",
            privatnost=0
        )
        kor.set_lozinka("Petar123!")
        kor.save()

        koruser = User.objects.create(
            username="reguser"
        )
        koruser.set_password("Petar123!")
        koruser.save()

        self.client = Client()

    def test_korisnik_uspesna_prijava(self):
        print("Test3")
        response = self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "reguser",
                "lozinka": "Petar123!"
            },
            follow=True
        )

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "reguser")
        self.assertEqual(self.client.session["tip"], TIP_KORISNIK)

    def test_korisnik_neuspesna_prijava(self):
        print("test 4")
        response = self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "reguser",
                "lozinka": "PogresnaLozinka!"
            },
            follow=True
        )

        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_korisnik_uspesan_pristup_profilu(self):
        self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "reguser",
                "lozinka": "Petar123!"
            }
        )

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_korisnik_ne_moze_pristupiti_moderator_delu(self):
        self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "reguser",
                "lozinka": "Petar123!"
            }
        )

        response = self.client.get(
            reverse(
                "izmena_igre",
                kwargs={"igra_id": self.igra.pk}
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("igre"))

    def test_korisnik_ne_moze_pristupiti_admin_delu(self):
        self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "reguser",
                "lozinka": "Petar123!"
            }
        )

        response = self.client.get(reverse("admin_users"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/prijava/", response.url)

    

    def test_moderator_uspesna_prijava(self):
        response = self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "moduser",
                "lozinka": "Djole123!"
            },
            follow=True
        )

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "moduser")
        self.assertEqual(self.client.session["tip"], TIP_MODERATOR)


    def test_moderator_neuspesna_prijava(self):
        response = self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "moduser",
                "lozinka": "LosaLozinka123!"
            },
            follow=True
        )

        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_moderator_moze_pristupiti_izmeni_igre(self):
        self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "moduser",
                "lozinka": "Djole123!"
            }
        )

        response = self.client.get(
            reverse(
                "izmena_igre",
                kwargs={"igra_id": self.igra.pk}
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_moderator_ne_moze_pristupiti_admin_delu(self):
        self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "moduser",
                "lozinka": "Djole123!"
            }
        )

        response = self.client.get(reverse("admin_games"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/prijava/", response.url)

    def test_moderator_uspesna_odjava(self):
        self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "moduser",
                "lozinka": "Djole123!"
            }
        )

        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.get(
            reverse("odjava"),
            follow=True
        )

        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)

    
    def test_admin_uspesna_prijava(self):
        response = self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "adminuser",
                "lozinka": "Admin123!"
            },
            follow=True
        )

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(
            response.wsgi_request.user.username,
            "adminuser"
        )
        self.assertEqual(
            self.client.session["tip"],
            TIP_ADMIN
        )

    def test_admin_neuspesna_prijava(self):
        response = self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "adminuser",
                "lozinka": "LosaLozinka123!"
            },
            follow=True
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )
        self.assertNotIn(
            "_auth_user_id",
            self.client.session
        )
    def test_admin_moze_pristupiti_admin_delu(self):
        self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "adminuser",
                "lozinka": "Admin123!"
            }
        )

        self.assertTrue(
            "_auth_user_id" in self.client.session
        )
        self.assertEqual(
            self.client.session.get("tip"),
            TIP_ADMIN
        )

        response = self.client.get(reverse("admin_users"))

        self.assertEqual(response.status_code, 200)

    def test_admin_uspesna_odjava(self):
        self.client.post(
            reverse("prijava"),
            data={
                "korisnicko_ime": "adminuser",
                "lozinka": "Admin123!"
            }
        )

        self.assertIn(
            "_auth_user_id",
            self.client.session
        )

        response = self.client.get(
            reverse("odjava"),
            follow=True
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )
        self.assertNotIn(
            "_auth_user_id",
            self.client.session
        )

class RegistracijaTestCase(TestCase):

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.url = reverse("registracija")

        self.ispravni_podaci = {
            "ime": "Nikola",
            "prezime": "Nikolic",
            "korisnicko_ime": "novikorisnik",
            "email": "novikorisnik@gmail.com",
            "lozinka": "Nikola123!",
            "potvrda_lozinke": "Nikola123!"
        }

        postojeci_korisnik = Korisnik.objects.create(
            korisnickoime="postojeci",
            email="postojeci@gmail.com",
            tip=TIP_KORISNIK,
            ime="Petar",
            prezime="Petrovic",
            privatnost=0
        )
        postojeci_korisnik.set_lozinka("Petar123!")
        postojeci_korisnik.save()

        django_user = User.objects.create(
            username="postojeci"
        )
        django_user.set_password("Petar123!")
        django_user.save()
    


    def test_uspesna_registracija(self):
        response = self.client.post(
            self.url,
            data=self.ispravni_podaci,
            follow=True
        )

        self.assertTrue(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        )

        self.assertTrue(
            User.objects.filter(
                username="novikorisnik"
            ).exists()
        )

        registrovani = Korisnik.objects.get(
            korisnickoime="novikorisnik"
        )

        self.assertEqual(registrovani.tip, TIP_KORISNIK)

        # Posle uspešne registracije korisnik je na login stranici
        self.assertEqual(
            response.request["PATH_INFO"],
            reverse("prijava")
        )
        self.assertContains(response, "Uspešna registracija")

    def test_registracija_korisnicko_ime_vec_postoji(self):
        podaci = self.ispravni_podaci.copy()
        podaci["korisnicko_ime"] = "postojeci"

        response = self.client.post(
            self.url,
            data=podaci,
            follow=True
        )

        # Nije kreiran još jedan korisnik sa istim imenom
        self.assertEqual(
            Korisnik.objects.filter(
                korisnickoime="postojeci"
            ).count(),
            1
        )

        self.assertContains(
            response,
            "Korisničko ime je zauzeto"
        )


    def test_registracija_lozinke_se_ne_podudaraju(self):
        podaci = self.ispravni_podaci.copy()
        podaci["potvrda_lozinke"] = "DrugaLozinka123!"

        response = self.client.post(
            self.url,
            data=podaci,
            follow=True
        )

        self.assertFalse(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        )

        self.assertContains(
            response,
            "Lozinke se ne poklapaju"
        )


    def test_registracija_neispravan_format_lozinke(self):
        podaci = self.ispravni_podaci.copy()
        podaci["lozinka"] = "nikola"
        podaci["potvrda_lozinke"] = "nikola"

        response = self.client.post(
            self.url,
            data=podaci,
            follow=True
        )

        self.assertFalse(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        )

        self.assertContains(
            response,
            "Lozinka mora imati min. 8 karaktera, jedno veliko i malo slovo, broj i specijalan znak."
        )

    def test_registracija_prazno_obavezno_polje(self):
        podaci = self.ispravni_podaci.copy()
        podaci["ime"] = ""

        response = self.client.post(
            self.url,
            data=podaci,
            follow=True
        )

        self.assertFalse(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        )

        self.assertContains(
            response,
            "Sva polja su obavezna"
        )
    

class SeleniumRegistracijaTestCase(StaticLiveServerTestCase):

    def setUp(self):
        super().setUp()

        # postojeći korisnik za test zauzetog korisničkog imena
        postojeci = Korisnik.objects.create(
            korisnickoime="postojeci",
            email="postojeci@gmail.com",
            tip=TIP_KORISNIK,
            ime="Petar",
            prezime="Petrovic",
            privatnost=0,
            obrisan=0
        )
        postojeci.set_lozinka("Petar123!")
        postojeci.save()

        postojeci_user = User.objects.create(
            username="postojeci"
        )
        postojeci_user.set_password("Petar123!")
        postojeci_user.save()


        #Promeniti putanju za main project
        service = webdriver.ChromeService(
            executable_path=(
                "C:\\Users\\Dare\\Desktop\\New Folder (14)\\"
                "Final_Implementations\\\Tabletop_Tracker_1.0_untested\\chromedriver.exe"
            )
        )

        self.browser = webdriver.Chrome(service=service)
        self.browser.implicitly_wait(10)
        self.appURL = self.live_server_url + "/igre/"

    def tearDown(self):
        self.browser.quit()
        super().tearDown()

    #Reusable funkcije koje se pojavljuju na svakom registracija testu
    def otvori_registraciju(self):
        self.browser.get(self.appURL)

        # Otvaranje menija
        self.browser.find_element(
            By.CLASS_NAME,
            "dropdown-toggle"
        ).click()

        # Odlazak na login
        self.browser.find_element(
            By.LINK_TEXT,
            "Login"
        ).click()

        # Odlazak sa login stranice na registraciju
        self.browser.find_element(
            By.LINK_TEXT,
            "Registruj se"
        ).click()

        self.assertIn(
            "/registracija/",
            self.browser.current_url
        )
    #slanje informacija za registraciju
    def popuni_formu(
        self,
        ime="Nikola",
        prezime="Nikolic",
        korisnicko_ime="novikorisnik",
        email="novikorisnik@gmail.com",
        lozinka="Nikola123!",
        potvrda_lozinke="Nikola123!"
    ):
        self.browser.find_element(
            By.NAME,
            "ime"
        ).send_keys(ime)

        self.browser.find_element(
            By.NAME,
            "prezime"
        ).send_keys(prezime)

        self.browser.find_element(
            By.NAME,
            "korisnicko_ime"
        ).send_keys(korisnicko_ime)

        self.browser.find_element(
            By.NAME,
            "email"
        ).send_keys(email)

        self.browser.find_element(
            By.NAME,
            "lozinka"
        ).send_keys(lozinka)

        self.browser.find_element(
            By.NAME,
            "potvrda_lozinke"
        ).send_keys(potvrda_lozinke)

    
    def potvrdi_registraciju(self):
        self.browser.find_element(
            By.CSS_SELECTOR,
            'button[type="submit"]'
        ).click()

    def test_selenium_uspesna_registracija(self):
        self.otvori_registraciju()

        self.popuni_formu()

        self.potvrdi_registraciju()

        WebDriverWait(self.browser, 10).until(
            EC.url_contains("/prijava/")
        )

        self.assertIn(
            "/prijava/",
            self.browser.current_url
        )

        self.assertTrue(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        ) 
    def test_selenium_korisnicko_ime_vec_postoji(self):
        self.otvori_registraciju()

        self.popuni_formu(
            korisnicko_ime="postojeci",
            email="noviemail@gmail.com"
        )

        self.potvrdi_registraciju()

        self.assertIn(
            "Korisničko ime je zauzeto",
            self.browser.page_source
        )

        self.assertEqual(
            Korisnik.objects.filter(
                korisnickoime="postojeci"
            ).count(),
            1
        )

        self.assertIn(
            "/registracija/",
            self.browser.current_url
        )


    def test_selenium_lozinke_se_ne_podudaraju(self):
        self.otvori_registraciju()

        self.popuni_formu(
            lozinka="Nikola123!",
            potvrda_lozinke="Petar123!"
        )

        self.potvrdi_registraciju()

        client_error = self.browser.find_element(
            By.ID,
            "clientError"
        )

        self.assertIn(
            "Lozinke se ne poklapaju",
            client_error.text
        )

        self.assertFalse(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        )

        self.assertIn(
            "/registracija/",
            self.browser.current_url
        )

    def test_selenium_neispravan_email(self):
        self.otvori_registraciju()

        self.popuni_formu(
            email="neispravan-email.com"
        )

        self.potvrdi_registraciju()

        email_polje = self.browser.find_element(
            By.NAME,
            "email"
        )

        email_validan = self.browser.execute_script(
            "return arguments[0].checkValidity();",
            email_polje
        )

        poruka = email_polje.get_attribute(
            "validationMessage"
        )

        self.assertFalse(email_validan)
        self.assertNotEqual(poruka, "")

        self.assertFalse(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        )

        self.assertIn(
            "/registracija/",
            self.browser.current_url
        )

    def test_selenium_neispravan_format_lozinke(self):
        self.otvori_registraciju()

        self.popuni_formu(
            lozinka="nikola",
            potvrda_lozinke="nikola"
        )

        self.potvrdi_registraciju()

        client_error = self.browser.find_element(
            By.ID,
            "clientError"
        )

        self.assertIn(
            "Format lozinke nije ispravan",
            client_error.text
        )

        self.assertFalse(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        )

        self.assertIn(
            "/registracija/",
            self.browser.current_url
        )

    def test_selenium_prazno_obavezno_polje(self):
        self.otvori_registraciju()

        # Namerno ne popunjavamo ime
        self.browser.find_element(
            By.NAME,
            "prezime"
        ).send_keys("Nikolic")

        self.browser.find_element(
            By.NAME,
            "korisnicko_ime"
        ).send_keys("novikorisnik")

        self.browser.find_element(
            By.NAME,
            "email"
        ).send_keys("novikorisnik@gmail.com")

        self.browser.find_element(
            By.NAME,
            "lozinka"
        ).send_keys("Nikola123!")

        self.browser.find_element(
            By.NAME,
            "potvrda_lozinke"
        ).send_keys("Nikola123!")

        self.potvrdi_registraciju()

        ime_polje = self.browser.find_element(
            By.NAME,
            "ime"
        )

        ime_validno = self.browser.execute_script(
            "return arguments[0].checkValidity();",
            ime_polje
        )

        poruka = ime_polje.get_attribute(
            "validationMessage"
        )

        self.assertFalse(ime_validno)
        self.assertNotEqual(poruka, "")

        self.assertFalse(
            Korisnik.objects.filter(
                korisnickoime="novikorisnik"
            ).exists()
        )

        self.assertIn(
            "/registracija/",
            self.browser.current_url
        )   
