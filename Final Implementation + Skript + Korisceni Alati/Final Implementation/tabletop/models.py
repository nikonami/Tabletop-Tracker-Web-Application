# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.auth.models import User
from django.db import models
import hashlib #Sofija - Hashing the passwords

class Dostignuca(models.Model):
    """
    **MODELI**

    Modelira dostignuca koji korisnik moze da postigne, Tabela koristi strani kompozitni primarni kljuc
    kao strani kljuc u tabeli, ali posto Django limitira ovu mogucnost pravi model razdvaja taj kljuc na
    dva Integer fielda koja su popunjeni koristeci ForeignObject klasom. Tabela prati svoj primarni kljuc,
    kao i naziv, uslov(operator funkcije) i vrednost za dostici. Takodje, model prati i ko je kreirao i kada.

    **Srodni modeli**

    :model:`tabletop.statistika`
    """
    vrednostzadostici = models.CharField(db_column='VrednostZaDostici', max_length=40)  # Field name made lowercase.
    naziv = models.CharField(db_column='Naziv', max_length=20)  # Field name made lowercase.
    uslov = models.CharField(db_column='Uslov', max_length=20, blank=True, null=True)  # Field name made lowercase.
    kreirao = models.ForeignKey('Korisnik', models.DO_NOTHING, db_column='Kreirao', blank=True, null=True)  # Field name made lowercase.
    datumkreiranja = models.DateTimeField(db_column='DatumKreiranja', blank=True, null=True)  # Field name made lowercase.
    slikaurl = models.CharField(db_column='slikaURL', max_length=255, blank=True, null=True)  # Field name made lowercase.
    iddos = models.AutoField(db_column='IDDos', primary_key=True)  # Field name made lowercase.
    idigre = models.IntegerField()
    idsta = models.IntegerField()  # Field name made lowercase.
    statistic = models.ForeignObject('Statistika', models.DO_NOTHING, from_fields=("idsta", "idigre"),
                                     to_fields=("idsta", "idigre"))

    #=========== Masa
    opis = models.CharField(db_column='Opis', max_length=255, blank=True, null=True)
    #===========

    def get_igra_by_id(self):
        try:
            return Igra.objects.get(idigre=self.idigre).naziv
        except ValueError:
            return None

    class Meta:
        managed = True
        db_table = 'dostignuca'


class Igra(models.Model):
    """
    **MODEL**

    Modelira igre u MySQL bazi podataka. Svaka igra ima informacije o sebi(naziv, godina proizvodnje, opis itd.)
    kao i povezanu sliku i video tutorial koji se prikazuju na njenoj stranici. Igra moze biti 'soft-delete'-ovana
    tako sto se field obrisan postavi na 1, time cineti igru nevidljivim.
    """
    idigre = models.AutoField(db_column='IDIgre', primary_key=True)  # Field name made lowercase.
    promenio = models.ForeignKey('Korisnik', models.DO_NOTHING, db_column='Promenio', blank=True, null=True)  # Field name made lowercase.
    naziv = models.CharField(db_column='Naziv', max_length=100)  # Field name made lowercase.
    godinaproizvodnje = models.DateTimeField(db_column='GodinaProizvodnje')  # Field name made lowercase.
    minigraca = models.IntegerField(db_column='minIgraca')  # Field name made lowercase.
    maxigraca = models.IntegerField(db_column='maxIgraca')  # Field name made lowercase.
    opis = models.CharField(db_column='Opis', max_length=100)  # Field name made lowercase.
    slikaurl = models.CharField(db_column='slikaURL', max_length=255)  # Field name made lowercase.
    videotutorialurl = models.CharField(db_column='videoTutorialURL', max_length=255)  # Field name made lowercase.
    datumizmene = models.DateTimeField(db_column='DatumIzmene', blank=True, null=True)  # Field name made lowercase.
    obrisan = models.IntegerField(db_column='Obrisan', blank=True, null=True)  # Field name made lowercase.
    zanr = models.CharField(db_column='Zanr', max_length=30, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'igra'

    #===== Sofija
    def __str__(self):
        return self.naziv
    #======


class Korisnik(models.Model):
    """
    **MODEL**

    Model korisnika u MySQL bazi. Spaja se sa Django kreiranom Users modelom kako bi se kontrolisao
    pristup sistemu. Preko modela korisnik moze promeniti informacije o sebi koje nisu u
    Django modelu, kao i da bude 'soft-delete'-ovan tako sto se postavi obrisan na 1, time
    taj korisnik nece biti vidljiv i moci da udje u sistem.
    s
    """
    #============Sofija
    TIP_GOST = 0
    TIP_KORISNIK = 1
    TIP_MODERATOR = 2
    TIP_ADMINISTRATOR = 3
    #==============

    idkor = models.AutoField(db_column='IDKor', primary_key=True)  # Field name made lowercase.
    promenio = models.ForeignKey('self', models.DO_NOTHING, db_column='Promenio', blank=True, null=True)  # Field name made lowercase.
    korisnickoime = models.CharField(db_column='KorisnickoIme', max_length=30)  # Field name made lowercase.
    lozinka = models.CharField(db_column='Lozinka', max_length=40)  # Field name made lowercase.
    email = models.CharField(max_length=50)
    tip = models.IntegerField(db_column='Tip')  # Field name made lowercase.
    ime = models.CharField(db_column='Ime', max_length=20)  # Field name made lowercase.
    prezime = models.CharField(db_column='Prezime', max_length=20)  # Field name made lowercase.
    datumizmene = models.DateTimeField(db_column='DatumIzmene', blank=True, null=True)  # Field name made lowercase.
    obrisan = models.IntegerField(db_column='Obrisan', blank=True, null=True)  # Field name made lowercase.
    privatnost = models.IntegerField(db_column='Privatnost')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'korisnik'
    #========= Sofija
    def set_lozinka(self, lozinka_plain):
        self.lozinka = hashlib.sha1(lozinka_plain.encode('utf-8')).hexdigest()

    def proveri_lozinku(self, lozinka_plain):
        return self.lozinka == hashlib.sha1(lozinka_plain.encode('utf-8')).hexdigest()

    def je_admin(self):
        return self.tip == self.TIP_ADMINISTRATOR

    def je_moderator(self):
        return self.tip == self.TIP_MODERATOR

    def __str__(self):
        return self.korisnickoime
    #==============Sofija

    #=============================== Connection to user django model
    #user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    #==================================================================

class Korisnikdostignuca(models.Model):
    """
    **MODEL**

    Ovaj model modelira pracenje kada korisnik je dostigao neko Dostignuce. Model se spaja sa
    vodjenom statistikom koja je presla vrednost za dostici u nekom Dostignucu. To se spaja sa
    tim dostignucem kako bi se lakse priakzalo na stranici korisnika. Takodje, prati se datum
    kada se ovo dostiglo kao i privatnost ovog dostignuca koji korisnik moze da promeni

    **Srodni modeli**

    :model:`tabletop.vodjenadostignuca`

    :model:`tabletop.dostignuca`

    """
    datum = models.DateTimeField(db_column='Datum')  # Field name made lowercase.
    idvodj = models.OneToOneField('Vodjenastatistika', models.DO_NOTHING, db_column='IDVodj', primary_key=True)  # Field name made lowercase.
    privatnost = models.IntegerField(db_column='privatnost')
    dostignuce = models.ForeignKey(Dostignuca, models.DO_NOTHING, db_column='dostignuce', default=None)

    class Meta:
        managed = True
        db_table = 'korisnikdostignuca'


class Listaigara(models.Model):
    """
    **MODEL**

    Modelira liste igara koji korisnici mogu da naprave. Svaki diskretan deo liste (tj, pojedinacna igra u nekoj listi)
    za nekog korisnika se dodaje u tabelu sa svojim identifikatorom, gde se onda lista moze grupisati po
    nazivu liste, dok id spcificnog elementa liste i id korisnika koji je napravio formiraju kompozitini
    primarni kljuc za ovu tabelu. Privatnost ove liste se prati za svaki element.

    **Srodni model**

    :model:`tabletop.korisnik`

    :model:`tabletop.igra`

    """
    pk = models.CompositePrimaryKey('idliste', 'idkor')
    idliste = models.IntegerField(db_column='IDListe')  # Field name made lowercase.
    idkor = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='IDKor')  # Field name made lowercase.
    idigre = models.ForeignKey(Igra, models.DO_NOTHING, db_column='IDIgre')  # Field name made lowercase.
    nazivliste = models.CharField(db_column='NazivListe', max_length=30)  # Field name made lowercase.
    privatnost = models.IntegerField(db_column='Privatnost')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'listaigara'


class Prijatelji(models.Model):
    """
    **MODEL**

    Modelira prijatelstva i zahteve za prijatelstva izmedju dva korisnika. Idkor2 prati koji korisnik
    prima zahtev za prijatelstvo, dok Idkor1 prati ko je poslao taj zahtev, a ova dva kljuca formiraju
    kompozitni primarni kljuc za ovu tabelu. 0 u statuszahteva predstavlja zahtev koji nije prihvatan jos,
    dok 1 predstavlja prihvacen zahtev i prijatelstvo.

    **Srodni modeli**

    :model:`tabletop.korisnik`
    """
    pk = models.CompositePrimaryKey('idkor2', 'idkor1')
    idkor2 = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='IDKor2')  # Field name made lowercase.
    idkor1 = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='IDKor1', related_name='prijatelji_idkor1_set')  # Field name made lowercase.
    statuszahteva = models.IntegerField(db_column='statusZahteva')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'prijatelji'


class Statistika(models.Model):
    """
    **MODEL**

    Modelira statistike o igri u MySQL bazi. Statistika je spojena sa igrom i opisuje statistika koja
    moze da se prati o toj igri (npr. broj pobeda). 4 tipa statistike postoje, Numericke, Tekstualne,
    Da/Ne, i statistike sa diskretnim opcijama (dropdown, po tome da se koristi dropdown meni da se
    prikazuju). Dropdown statistika specificno prati svoje opcije u dropdown field-u, koristeci
    comma-seperated String, i ima ugradjenu funkciju da odvoji ovaj string po zarezima.
    Takodje, tabela moze da prati ko je kreirao i kada  (od moderatora ili admina).

    **Srodni modeli**

    :model:`tabletop.igra`
    """
    pk = models.CompositePrimaryKey('idsta', 'idigre')
    idsta = models.IntegerField(db_column='IDSta')  # Field name made lowercase.
    idigre = models.ForeignKey(Igra, models.DO_NOTHING, db_column='IDIgre')  # Field name made lowercase.
    kreirao = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='Kreirao', blank=True, null=True)  # Field name made lowercase.
    datumkreiranja = models.DateTimeField(db_column='DatumKreiranja', blank=True, null=True)  # Field name made lowercase.
    naziv = models.CharField(db_column='Naziv', max_length=50)  # Field name made lowercase.
    tip = models.CharField(db_column='Tip', max_length=30)  # Field name made lowercase.
    opis = models.CharField(db_column='Opis', max_length=20, blank=True, null=True)  # Field name made lowercase.
    dropdown = models.CharField(db_column='DropDown', max_length=200, blank=True, null=True)  # Field name made lowercase.
    tipgrafikona = models.CharField(db_column='TipGrafikona', max_length=20, null=True, blank=True)
    #============================= Masa
    # polja za numericki tip statistike
    minvrednost = models.FloatField(db_column='minVrednost', null=True, blank=True)
    maxvrednost = models.FloatField(db_column='maxVrednost', null=True, blank=True)
    jedinicamere = models.CharField(db_column='jedinicaMere', max_length=50, null=True, blank=True)
    # polja za tekstualni tip statistike
    maxduzinateksta = models.IntegerField(db_column='maxDuzinaTeksta', null=True, blank=True)
    placeholdertekst = models.CharField(db_column='placeholderTekst', max_length=255, null=True, blank=True)
    # polje za da/ne tip statistike'
    podrazumevanavrednost = models.CharField(db_column='podrazumevanaVrednost', max_length=3, null=True, blank=True)

    def __str__(self):
        return self.naziv
    #=================================================
    def seperate_dropdown(self):
        return [item.strip() for item in self.dropdown.split(',')]
    class Meta:
        managed = True
        db_table = 'statistika'


class Utisak(models.Model):
    """
    **MODEL**

    Modelira utiske koji korisnici mogu da ostave na stranici igre. Strani kljucevi Igre i korisnika
    formiraju kompozitni primarni kljuc ove tabele. Opis koji je korisnik ostavio, kao i ocena se prate
    u tabeli. Takodje, posto moderator moze da izmenjuje ove utiske, prati se koj moderator je promenio
    utisak, kao i razlog izmene, datum te izmene, i status te izmene, tj. kako je promenio tabelu.

    **Srodni modeli**

    :model:`tabletop.igra`

    :model:`tabletop.korisnik`
    """
    pk = models.CompositePrimaryKey('idigre', 'idkor')
    idigre = models.ForeignKey(Igra, models.DO_NOTHING, db_column='IDIgre')  # Field name made lowercase.
    idkor = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='IDKor')  # Field name made lowercase.
    promenio = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='Promenio', related_name='utisak_promenio_set', blank=True, null=True)  # Field name made lowercase.
    opis = models.CharField(db_column='Opis', max_length=300)  # Field name made lowercase.
    ocena = models.IntegerField(db_column='Ocena')  # Field name made lowercase.
    datumizmene = models.DateTimeField(db_column='DatumIzmene', blank=True, null=True)  # Field name made lowercase.
    razlogizmene = models.CharField(db_column='RazlogIzmene', max_length=50, blank=True, null=True)  # Field name made lowercase.
    statusizmene = models.IntegerField(db_column='StatusIzmene', blank=True, null=True)  # Field name made lowercase.

    #============== Masa
    originalniopis = models.CharField(db_column='OriginalniOpis', max_length=300, blank=True, null=True)
    #===============

    class Meta:
        managed = True
        db_table = 'utisak'


class Vodjenastatistika(models.Model):
    """
    **MODEL**

    Modelira svaku vodjenu statistiku o korisniku u MySQL bazi. Svaki put kada korisnik promeni neku
    statistiku o igri, napravi se nova vodjena statistika u bazi sa datumom kreiranja kako bi se
    moglo prikazati kasnije graph statistike preko vremena. Svaka vodjena statistika prati vrednost,
    tekst, i svoju privatnost koju korisnik moze da promeni. Dok statistika ima svoji primarni kljuc,
    ima takodje strani kljuc od model statistika koja ima kompozitni primarni kljuc. Time sto django
    ne ume da modelira ovo, koriste se dva IntegerField-a sa ForeignObject klasom da im dodeli vrednosti
    iz modela statistika.

    **Srodni modeli**

    :model:`tabletop.statistika`

    :model:`tabletop.korisnik`
    """
    vrednost = models.CharField(db_column='Vrednost', max_length=100)  # Field name made lowercase.
    datum = models.DateTimeField(db_column='Datum')  # Field name made lowercase.
    tekst = models.CharField(db_column='Tekst', max_length=30, blank=True, null=True)  # Field name made lowercase.
    idvodj = models.AutoField(db_column='IDVodj', primary_key=True)  # Field name made lowercase.
    idkor = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='IDKor', blank=True, null=True)  # Field name made lowercase.
    idigre=models.IntegerField()
    idsta=models.IntegerField()
    statistic = models.ForeignObject('Statistika', models.DO_NOTHING, from_fields=("idsta","idigre"), to_fields=("idsta", "idigre"))
    privatnost = models.IntegerField(db_column='Privatnost')

    class Meta:
        managed = True
        db_table = 'vodjenastatistika'
