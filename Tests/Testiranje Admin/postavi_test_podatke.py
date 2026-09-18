# postavi_test_podatke.py
#
# Skripta koja:
#   1. BRISE sve podatke iz baze (redosledom koji postuje foreign key ogranicenja)
#   2. Ubacuje sve potrebne test podatke za Selenium i Django jedinicne testove
#
# Pokretanje (iz root foldera projekta, gde je manage.py):
#   python manage.py shell < postavi_test_podatke.py
#
# ILI kao management komanda:
#   python manage.py shell
#   >>> exec(open('postavi_test_podatke.py').read())

import hashlib
from django.contrib.auth.models import User
from tabletop.models import (
    Korisnik, Igra, Utisak, Prijatelji,
    Listaigara, Vodjenastatistika, Korisnikdostignuca,
    Dostignuca, Statistika
)

def hesiraj(lozinka_plain):
    """SHA1 hesiranje lozinke — isto kao u views.py (hash_pw funkcija)."""
    return hashlib.sha1(lozinka_plain.encode('utf-8')).hexdigest()

# ===========================================================================
# KORAK 1: BRISANJE SVIH PODATAKA
# Redosled je vazan — brišemo prvo tabele koje imaju strane kljuceve
# ka drugim tabelama, pa tek onda roditeljske tabele.
# ===========================================================================

print("Brisanje podataka...")

Korisnikdostignuca.objects.all().delete()
print("  - korisnikdostignuca: obrisano")

Vodjenastatistika.objects.all().delete()
print("  - vodjenastatistika: obrisano")

Dostignuca.objects.all().delete()
print("  - dostignuca: obrisano")

Statistika.objects.all().delete()
print("  - statistika: obrisano")

Utisak.objects.all().delete()
print("  - utisak: obrisano")

Listaigara.objects.all().delete()
print("  - listaigara: obrisano")

Prijatelji.objects.all().delete()
print("  - prijatelji: obrisano")

Igra.objects.all().delete()
print("  - igra: obrisano")

Korisnik.objects.all().delete()
print("  - korisnik: obrisano")

User.objects.all().delete()
print("  - django User: obrisano")

print("Brisanje zavrseno.\n")

# ===========================================================================
# KORAK 2: KREIRANJE TEST PODATAKA
# ===========================================================================

print("Kreiranje test podataka...")

# ---------------------------------------------------------------------------
# KORISNICI
# ---------------------------------------------------------------------------
# --- ADMIN ---
admin = Korisnik.objects.create(
    korisnickoime='testadmin',
    lozinka=hesiraj('Admin123!'),
    email='admin@test.com',
    tip=3,                          # mora biti 3, ne 2! (decorator.py: TIP_ADMIN = 3)
    ime='Nikola',
    prezime='Adminovic',
    privatnost=0,
    obrisan=0,
)
User.objects.create_user(username='testadmin', password='Admin123!')
print(f"  + Admin: testadmin / Admin123!")

# --- MODERATOR ---
moderator = Korisnik.objects.create(
    korisnickoime='testmoderator',
    lozinka=hesiraj('Moder123!'),
    email='moderator@test.com',
    tip=2,                          # tip=2 je moderator (TIP_ADMINISTRATOR u models.py, ali ovo je moderator u praksi)
    ime='Jovana',
    prezime='Moderovic',
    privatnost=0,
    obrisan=0,
)
User.objects.create_user(username='testmoderator', password='Moder123!')
print(f"  + Moderator: testmoderator / Moder123!")

# --- OBICAN KORISNIK 1 (za test brisanja - ovaj ce biti obrisan u Selenium testu!) ---
korisnik_za_brisanje = Korisnik.objects.create(
    korisnickoime='korisnik_brisanje',
    lozinka=hesiraj('Korisnik123!'),
    email='brisanje@test.com',
    tip=0,
    ime='Marko',
    prezime='Markovic',
    privatnost=0,
    obrisan=0,
)
User.objects.create_user(username='korisnik_brisanje', password='Korisnik123!')
print(f"  + Korisnik za brisanje: korisnik_brisanje / Korisnik123!")

# --- OBICAN KORISNIK 2 (za test promene podataka) ---
korisnik_za_promenu = Korisnik.objects.create(
    korisnickoime='korisnik_promena',
    lozinka=hesiraj('Promena123!'),
    email='promena@test.com',
    tip=0,
    ime='Ana',
    prezime='Anic',
    privatnost=0,
    obrisan=0,
)
User.objects.create_user(username='korisnik_promena', password='Promena123!')
print(f"  + Korisnik za promenu: korisnik_promena / Promena123!")

# --- OBICAN KORISNIK 3 (za test "vec postojece korisnicko ime") ---
korisnik_zauzeto = Korisnik.objects.create(
    korisnickoime='zauzeto_ime',
    lozinka=hesiraj('Zauzeto123!'),
    email='zauzeto@test.com',
    tip=0,
    ime='Petar',
    prezime='Petrovic',
    privatnost=0,
    obrisan=0,
)
User.objects.create_user(username='zauzeto_ime', password='Zauzeto123!')
print(f"  + Korisnik sa zauzetim imenom: zauzeto_ime / Zauzeto123!")

# --- OBICAN KORISNIK 4 (generalni, za listanje u admin panelu) ---
korisnik_opsti = Korisnik.objects.create(
    korisnickoime='obican_korisnik',
    lozinka=hesiraj('Obican123!'),
    email='obican@test.com',
    tip=0,
    ime='Milica',
    prezime='Milic',
    privatnost=0,
    obrisan=0,
)
User.objects.create_user(username='obican_korisnik', password='Obican123!')
print(f"  + Opsti korisnik: obican_korisnik / Obican123!")

print()

# ---------------------------------------------------------------------------
# IGRE
# ---------------------------------------------------------------------------
from datetime import datetime

# --- IGRA ZA BRISANJE (ovaj ce biti obrisan u Selenium testu!) ---
igra_za_brisanje = Igra.objects.create(
    naziv='TestIgraZaBrisanje',
    godinaproizvodnje=datetime(2019, 1, 1),
    minigraca=2,
    maxigraca=5,
    opis='Igra koja se koristi za testiranje brisanja.',
    slikaurl='http://example.com/brisanje.jpg',
    videotutorialurl='http://example.com/brisanje.mp4',
    obrisan=0,
    zanr='Strategija',
)
print(f"  + Igra za brisanje: TestIgraZaBrisanje")

# --- IGRE ZA LISTANJE (ostaju neobrisane, koriste se samo za prikaz u admin panelu) ---
igra_catan = Igra.objects.create(
    naziv='Catan',
    godinaproizvodnje=datetime(1995, 1, 1),
    minigraca=3,
    maxigraca=4,
    opis='Klasicna strategija sa ostrvima i resursima.',
    slikaurl='http://example.com/catan.jpg',
    videotutorialurl='http://example.com/catan.mp4',
    obrisan=0,
    zanr='Strategija',
)
print(f"  + Igra: Catan")

igra_wingspan = Igra.objects.create(
    naziv='Wingspan',
    godinaproizvodnje=datetime(2019, 1, 1),
    minigraca=1,
    maxigraca=5,
    opis='Igra o pticama i staklenim jajima.',
    slikaurl='http://example.com/wingspan.jpg',
    videotutorialurl='http://example.com/wingspan.mp4',
    obrisan=0,
    zanr='Porodicna',
)
print(f"  + Igra: Wingspan")

igra_ticket = Igra.objects.create(
    naziv='Ticket to Ride',
    godinaproizvodnje=datetime(2004, 1, 1),
    minigraca=2,
    maxigraca=5,
    opis='Izgradnja zeleznickih pruga sirom sveta.',
    slikaurl='http://example.com/ticket.jpg',
    videotutorialurl='http://example.com/ticket.mp4',
    obrisan=0,
    zanr='Porodicna',
)
print(f"  + Igra: Ticket to Ride")

print()

# ---------------------------------------------------------------------------
# UTISCI (potrebni da se testira brisanje korisnika — view brise i utiske)
# ---------------------------------------------------------------------------
Utisak.objects.create(
    idigre=igra_catan,
    idkor=korisnik_za_brisanje,
    opis='Odlicna igra, preporucujem svima!',
    ocena=5,
)
print(f"  + Utisak: korisnik_brisanje -> Catan")

Utisak.objects.create(
    idigre=igra_wingspan,
    idkor=korisnik_opsti,
    opis='Veoma lepa i opustajuca igra.',
    ocena=4,
)
print(f"  + Utisak: obican_korisnik -> Wingspan")

print()

# ---------------------------------------------------------------------------
# PRIJATELJI (potrebni da se testira brisanje korisnika — view brise i prijateljstva)
# ---------------------------------------------------------------------------
Prijatelji.objects.create(
    idkor1=korisnik_za_brisanje,
    idkor2=korisnik_opsti,
    statuszahteva=1,
)
print(f"  + Prijateljstvo: korisnik_brisanje <-> obican_korisnik")

print()
print("=" * 55)
print("Test podaci su uspesno postavljeni!")
print("=" * 55)
print()
print("KREDENCIJALI ZA TESTOVE:")
print(f"  Admin:              testadmin / Admin123!")
print(f"  Moderator:          testmoderator / Moder123!")
print(f"  Korisnik brisanje:  korisnik_brisanje / Korisnik123!")
print(f"  Korisnik promena:   korisnik_promena / Promena123!")
print(f"  Zauzeto ime:        zauzeto_ime / Zauzeto123!")
print(f"  Opsti korisnik:     obican_korisnik / Obican123!")
print()
print("IGRE:")
print(f"  Za brisanje:  TestIgraZaBrisanje")
print(f"  Ostale:       Catan, Wingspan, Ticket to Ride")
print()
print("UPOZORENJE: Nakon Selenium testova koji rade brisanje,")
print("ponovo pokreni ovu skriptu da resetujes podatke!")
