#Nikola Stamenkovic 2020/0723
from django import forms
from django.core.validators import validate_email
from tabletop.models import Korisnik
import pytz

class RecenzijaForm(forms.Form):
    opis = forms.CharField(label='opis', widget=forms.Textarea)
    rating = forms.IntegerField(label='rating', min_value=0, max_value=5)

class KorisnikForm(forms.ModelForm):
    korisnickoime = forms.CharField(required=False)
    lozinka = forms.CharField(required=False)
    email=forms.CharField(required=False)
    ime=forms.CharField(required=False)
    prezime=forms.CharField(required=False)
    class Meta:
        model = Korisnik
        fields = ['korisnickoime', 'lozinka', 'email', 'ime', 'prezime']
        exclude = ['idkor', 'promenio', 'tip', 'datumizmene', 'obrisan', 'privatnost']

    def clean(self):
        cleaned_data = super().clean()
        korisnickoime = cleaned_data.get("korisnickoime")
        lozinka = cleaned_data.get("lozinka")
        email = cleaned_data.get("email")

        if korisnickoime != "":
            existing_username = Korisnik.objects.filter(korisnickoime = korisnickoime)
            if existing_username.exists():
                self.add_error("korisnickoime", "Ime vec postoji") #return error
        #check password
        if email != "":
            try:
                validate_email(email)
            except ValueError:
                self.add_error("email", "Email nije u tacnom formatu") #return error

        return cleaned_data

#======================================= Masa Moderator
# Masa Jankovic 0462/19

# forme za moderatorske funkcionalnosti
# svaka forma odgovara jednoj stranici

from datetime import datetime, date, time
from django import forms
from .models import (
    Igra, Statistika, Dostignuca
)

# IZMENA IGRE

# lista zanrova
ZANR_CHOICES = [
    ('strategija', 'Strategija'),
    ('porodicna', 'Porodična igra'),
    ('zabavna', 'Zabavna igra (Party)'),
    ('kooperativna', 'Kooperativna igra'),
    ('kartaska', 'Kartaška igra'),
    ('apstraktna', 'Apstraktna igra'),
    ('tematska', 'Tematska igra'),
    ('ratna', 'Ratna igra'),
]


# forma za izmenu informacija o igri, prikazuje polja igre koje moderator moze da menja
# koristi se na stranici izmena_informacija_igre.html
# vezana je za model Igra
# validira da minimalan broj igraca nije veci od maksimalnog
class IgraForm(forms.ModelForm):
    # zanr se na stranici prikazuje kao dropdown meni, u bazi je tekst
    zanr = forms.ChoiceField(
        choices=ZANR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Žanr',
    )
    godinaproizvodnje = forms.IntegerField(
        label='Godina proizvodnje',
        min_value=1900,
        max_value=date.today().year,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Molimo ispravite označena polja.'},
    )

    class Meta:
        model = Igra
        fields = [
            'naziv',
            'zanr',
            'minigraca',
            'maxigraca',
            'opis',
            'slikaurl',
        ]

        widgets = {
            'naziv': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'minigraca': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            'maxigraca': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            'opis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 7,
            }),
            'slikaurl': forms.TextInput(attrs={
                'class': 'form-control',
            }),
        }

        labels = {
            'naziv': 'Naziv igre',
            'zanr': 'Žanr',
            'minigraca': 'Minimalan broj igrača',
            'maxigraca': 'Maksimalan broj igrača',
            'godinaproizvodnje': 'Godina proizvodnje',
            'opis': 'Opis igre',
            'slikaurl': 'URL slike igre',
        }

        error_messages = {
            'naziv': {'required': 'Molimo ispravite označena polja.'},
            'minigraca': {'required': 'Molimo ispravite označena polja.'},
            'maxigraca': {'required': 'Molimo ispravite označena polja.'},
            'godinaproizvodnje': {'required': 'Molimo ispravite označena polja.'},
            'opis': {'required': 'Molimo ispravite označena polja.'},
        }

    def __init__(self, *args, **kwargs):
        # popunjava pocetnu vrednost godine iz postojeceg datuma pri izmeni
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.godinaproizvodnje:
            self.initial['godinaproizvodnje'] = self.instance.godinaproizvodnje.year

    def clean(self):
        # validacija forme
        # da li je minigraca manje od maxigraca
        # vraca cleaned_data sa validiranim vrednostima ili ValidationError ako ne prodje validacija

        cleaned_data = super().clean()

        min_ig = cleaned_data.get('minigraca')
        max_ig = cleaned_data.get('maxigraca')
        if min_ig is not None and max_ig is not None:
            if min_ig > max_ig:
                raise forms.ValidationError(
                    'Molimo ispravite označena polja. Minimalan broj igrača ne može biti veći od maksimalnog.'
                )
        return cleaned_data

    def save(self, commit=True):
        # konvertuje int u datum pre upisa u bazu
        instance = super().save(commit=False)
        godina = self.cleaned_data.get('godinaproizvodnje')
        if godina:
            instance.godinaproizvodnje = datetime(godina, 1, 1, tzinfo=pytz.UTC)
        if commit:
            instance.save()
        return instance


# STATISTIKA

# tipovi statistike
TIP_STATISTIKE = [
    ('numericka', 'Numerička vrednost'),
    ('dropdown', 'Drop-down menu'),
    ('da_ne', 'Da/Ne'),
    ('tekstualna', 'Tekstualno polje'),
]

# tipovi grafikona za vizuelni prikaz statistike
TIP_GRAFIKONA = [
    ('bar', 'Bar chart'),
    ('pie', 'Pie chart'),
    ('line', 'Line graph'),
    ('column', 'Column chart'),
]


# forma za pravljenje statistike
# koristi se na stranici pravljenje_statistike.html
# vezana za model Statistika
class StatistikaForm(forms.ModelForm):
    # skriveno polje koje JS popunjava pre slanja forme
    # sadrzi dropdown opcije odvojene zarezima: Pobeda,Poraz,Nerešeno
    dropdown_opcije_tekst = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    # tip statistike, cuva se u polju 'tip' modela
    tip_stat = forms.ChoiceField(
        choices=TIP_STATISTIKE,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tip statistike',
    )

    # tip grafikona, cuva se kao tekst
    tip_grafikona = forms.ChoiceField(
        choices=TIP_GRAFIKONA,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tip grafičkog prikaza',
        required=False,
    )

    # dodatna polja za numericki tip statistike
    min_vrednost = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Minimalna vrednost',
    )
    max_vrednost = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Maksimalna vrednost',
    )
    jedinica_mere = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'poena, minuta, partija...',
        }),
        label='Jedinica mere',
    )

    # dodatna polja za tekstualni tip statistike
    max_duzina_teksta = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Maksimalna dužina teksta',
    )
    placeholder_tekst = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'npr. Unesite komentar o partiji',
        }),
        label='Placeholder tekst',
    )

    # podrazumevana vrednost za da/ne tip statistike
    podrazumevana_vrednost = forms.ChoiceField(
        choices=[('da', 'Da'), ('ne', 'Ne')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Podrazumevana vrednost',
    )

    class Meta:
        model = Statistika
        fields = ['naziv', 'opis']
        widgets = {
            'naziv': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'npr. Broj osvojenih poena',
            }),
            'opis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Unesite kratak opis statistike i načina praćenja.',
            }),
        }
        labels = {
            'naziv': 'Naziv statistike',
            'opis': 'Opis statistike',
        }
        error_messages = {
            'naziv': {'required': 'Naziv statistike je obavezan.'},
            'opis': {'required': 'Opis statistike je obavezan.'},
        }

    def __init__(self, *args, igra=None, **kwargs):
        # uzima igru kako bismo proverili jedinstvenost naziva statistike za tu igru
        self.igra = igra
        super().__init__(*args, **kwargs)
        self.fields['opis'].required = True

    def clean(self):
        # validacija za dropdown, mora da postoji bar jedna opcija
        # validacija jedinstvenosti naziva statistike za datu igru
        # validacija ako je numericka statistika da li je min < max
        # vraca: cleaned_data ili podize ValidationError

        cleaned_data = super().clean()

        # validacija za dropdown
        tip = cleaned_data.get('tip_stat')
        if tip == 'dropdown':
            opcije_tekst = cleaned_data.get('dropdown_opcije_tekst', '')
            opcije = [o.strip() for o in opcije_tekst.split(',') if o.strip()]
            if not opcije:
                raise forms.ValidationError(
                    'Morate dodati bar jednu opciju za drop-down statistiku.'
                )

        # validacija za naziv
        naziv = cleaned_data.get('naziv')
        if naziv and self.igra is not None:
            postoji = Statistika.objects.filter(idigre=self.igra, naziv=naziv)
            if self.instance and self.instance.pk:
                if not self.instance.pk == (None, None):
                    postoji = postoji.exclude(pk=self.instance.pk)
            if postoji.exists():
                raise forms.ValidationError(
                    'Statistika sa ovim nazivom već postoji za ovu igru. '
                    'Nazivi statistika za istu igru moraju biti jedinstveni.'
                )

        # validacija min < max
        if tip == 'numericka':
            min_v = cleaned_data.get('min_vrednost')
            max_v = cleaned_data.get('max_vrednost')
            if min_v is not None and max_v is not None and min_v > max_v:
                raise forms.ValidationError(
                    'Minimalna vrednost ne može biti veća od maksimalne.'
                )

        #validacija tip grafikona sa tip statistike
        if tip == 'numericka':
            grafikon = cleaned_data.get('tip_grafikona')
            if grafikon != 'line':
                raise forms.ValidationError(
                    'Numericka statistika mora da bude line-graph.'
                )
        elif tip != 'numericka':
            grafikon = cleaned_data.get('tip_grafikona')
            if grafikon == 'line':
                raise forms.ValidationError(
                    'Ne numericke statistike ne mogu da budu line-graph.'
                )

        return cleaned_data

    def save(self, commit=True):
        # cuva statistiku u bazi
        # pre cuvanja popunjava polje 'tip' i 'dropdown' iz extra polja forme koja nisu direktno u modelu

        instance = super().save(commit=False)

        # cuvamo podatke za statistiku
        instance.tip = self.cleaned_data.get('tip_stat', '')
        instance.tipgrafikona = self.cleaned_data.get('tip_grafikona')
        opcije_tekst = self.cleaned_data.get('dropdown_opcije_tekst', '')
        if opcije_tekst:
            instance.dropdown = opcije_tekst
        instance.minvrednost = self.cleaned_data.get('min_vrednost')
        instance.maxvrednost = self.cleaned_data.get('max_vrednost')
        instance.jedinicamere = self.cleaned_data.get('jedinica_mere')
        instance.maxduzinateksta = self.cleaned_data.get('max_duzina_teksta')
        instance.placeholdertekst = self.cleaned_data.get('placeholder_tekst')
        instance.podrazumevanavrednost = self.cleaned_data.get('podrazumevana_vrednost')

        if commit:
            instance.save()
        return instance


# ACHIEVEMENT

# operatori za uslov
USLOV_CHOICES = [
    ('>=', '>='),
    ('>', '>'),
    ('=', '='),
    ('<', '<'),
    ('<=', '<='),
]


# forma za pravljenje achievement-a
# koristi se na stranici pravljenje_dostignuca.html
# vezana za model Dostignuca
class DostignucaForm(forms.ModelForm):
    # operator uslova za dobijanje achievement-a
    uslov_operator = forms.ChoiceField(
        choices=USLOV_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Operator',
    )
    idsta = forms.ChoiceField(
        choices=[],
    )
    class Meta:
        model = Dostignuca
        # polja koja postoje u modelu Dostignuca
        fields = ['naziv', 'opis', 'idsta', 'vrednostzadostici', 'slikaurl']
        widgets = {
            'naziv': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Master Merlin',
            }),
            'opis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Kratak opis achievement-a.',
            }),
            'idsta': forms.Select(attrs={
                'class': 'form-select',
            }),
            'vrednostzadostici': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'npr. 10',
            }),
            'slikaurl': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...',
            }),
        }
        labels = {
            'naziv': 'Naziv achievement-a',
            'opis': 'Opis achievement-a',
            'idsta': 'Statistika za koju je vezan',
            'vrednostzadostici': 'Vrednost za dobijanje',
            'slikaurl': 'URL slike bedža',
        }
        error_messages = {
            'naziv': {'required': 'Morate uneti naziv achievement-a.'},
            'opis': {'required': 'Morate uneti opis achievement-a.'},
            'idsta': {'required': 'Morate odabrati statistiku.'},
            'vrednostzadostici': {'required': 'Morate uneti odgovarajuću vrednost za dobijanje achievement-a.'},
            'slikaurl': {'required': 'Slika bedža je obavezna'},
        }

    def __init__(self, *args, igra=None, **kwargs):
        # inicijalizacija forme
        # prima igra argument kako bi bili ograniceni samo na statistike te igre i za validaciju naziva
        # vraca instancu DostignucaForm
        super().__init__(*args, **kwargs)
        self.igra = igra.idigre
        self.fields['opis'].required = True
        self.fields['slikaurl'].required = True
        if igra:
            # prikazujemo samo statistike vezane za ovu igru
            #self.fields['idsta'].queryset = Statistika.objects.filter(idigre=igra.idigre)
            stats = Statistika.objects.filter(idigre=igra.idigre)
            stat_choices = []
            for stat in stats:
                stat_choices.append( (stat.idsta, str(stat.naziv)) )
            self.fields['idsta'].choices = stat_choices
            #print(self.fields['idsta'].choices)
            self.fields['idsta'].required = True

    def clean(self):
        # validacija jedinstvenosti naziva dostignuca za datu igru
        # vraca: cleaned_data ili podize ValidationError

        cleaned_data = super().clean()
        #print(cleaned_data.values())
        # validacija za naziv
        naziv = cleaned_data.get('naziv')
        if naziv and self.igra is not None:
            postoji = Dostignuca.objects.filter(idigre=self.igra, naziv=naziv)
            if self.instance and self.instance.pk:
                if not self.instance.pk == (None, None):
                    postoji = postoji.exclude(pk=self.instance.pk)
            if postoji.exists():
                raise forms.ValidationError(
                    'Dostignuće sa ovim nazivom već postoji za ovu igru. '
                    'Nazivi dostignuća za istu igru moraju biti jedinstveni.'
                )
        return cleaned_data

    def save(self, commit=True):
        # cuva achievement u bazi
        # pre cuvanja popunjava polje 'uslov' iz uslov_operator polja
        # vraca instancu Dostignuca modela
        instance = super().save(commit=False)
        instance.uslov = self.cleaned_data.get('uslov_operator', '')
        if commit:
            instance.save()
        return instance


# forme za upravljanje utiscima, tri odvojene forme za brisanje, filtriranje i skrivanje
# koriste se na stranici upravljanje_utiscima.html
class UtisakBrisanjeForm(forms.Form):
    # nije ModelForm, samo prikuplja podatke od moderatora, ne kreira nov objekat
    razlog_brisanja = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Unesite razlog brisanja utiska',
        }),
        label='Razlog brisanja',
        error_messages={'required': 'Razlog za izmenu je obavezan.'},
    )


class UtisakFiltriranjeForm(forms.Form):
    # prikuplja reci za filtriranje i razlog filtriranja
    reci_za_filtriranje = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'npr. reč1, reč2, reč3',
        }),
        label='Reči za filtriranje',
        required=False,
    )
    razlog_filtriranja = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Unesite razlog filtriranja utiska',
        }),
        label='Razlog filtriranja',
        error_messages={'required': 'Razlog za izmenu je obavezan.'},
    )


class UtisakSakrivanjeForm(forms.Form):
    # prikuplja razlog skrivanja utiska
    razlog_sakrivanja = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Unesite razlog za sakrivanje utiska',
        }),
        label='Razlog sakrivanja',
        error_messages={'required': 'Razlog za izmenu je obavezan.'},
    )

#==========================================================================================
