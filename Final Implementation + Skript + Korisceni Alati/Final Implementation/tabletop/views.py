#Nikola Stamenkovic 2020/0723
#============== XML Control
import xml
from xml.etree.ElementTree import XMLParser
#============== Password control
import hashlib
import re
#=============== Django Shortcuts
from django.shortcuts import render, redirect, get_object_or_404
#=============== Request Management and HTTP
import requests
from django.http import Http404
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.views.decorators.http import require_POST
#=============== DJANGO auth control
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
#=============== DJANGO utilities and contrib
from django.utils import timezone
from django.db.models import Subquery, OuterRef, Value, Avg
from django.templatetags.static import register
from django_stubs_ext import QuerySetAny
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
#=============== Other python utilities
from datetime import datetime
import functools
#============= User created files
from .forms import *
from .models import *
from .decorator import *

#privatnost - 0 private, 1 friend private, 2 public, 3 public front page
#prijateljstva - idkor1 posiljalac, idkor2 primalac

TIP_GOST = 0
TIP_KORISNIK = 1
TIP_MODERATOR = 2
TIP_ADMIN = 3
#========================= Masa
#status utiska vrednosti za povezivanje s bazom
STATUS_AKTIVAN = 0
STATUS_OBRISAN = 1
STATUS_FILTRIRAN = 2
STATUS_SAKRIVEN = 3
#================================================= Darko + Sofija
#temp hash ako ostane ovako na loginu
def hash_pw(password):
    """Hashuje lozinku algoritmom SHA-1. Vraća hex string dužine 40 karaktera."""
    return hashlib.sha1(password.encode("utf-8")).hexdigest()


#temp validacija ako ostane ovako za password
def validate_pw(password):
    """
    Proverava da li lozinka zadovoljava uslove:
    min. 8 karaktera, 1 veliko slovo, 1 malo slovo, 1 broj, 1 specijalan znak.
    """
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$"
    return bool(re.match(pattern, password))

#=========================================================================
#============================== VIEWS ===================================
def game_front_page_view(request):
    """
    **VIEW**

    Pogled na glavnu stranicu gde se sve igre prikazuju. Koristeci queryset dohvati sve igre koje
    nisu obrisane i posalje na front.

    ``Template``

    :template:`game_front_page.html`
    """

    #dohvati sve igre koje nisu obrisane
    igre = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0))
    return render(request, 'korisnik/game_front_page.html', {'igre':igre})

def game_page_view(request, name):
    """
    **VIEW**

    Pogled na individualno stranicu jedne igre. Stranica obuhvata dosta procesa. Prvo, dohvata
    svu informaciju sa BoardGameGeek website-a o ovoj igri i onda prikaze korisniku u lepo
    formatiranom obliku (jer prima u XML formatu). Zatim, omogucava ulogovanim korisnicima da
    ostave utiske o igri i da promene svoje vlasnistvo igre (tj. promeni da li je igrao, ima, ili wishlist-uje igru).
    Sa ove stranice korisnik moze takodje da ode na stranicu za azuriranje statistike o ovoj igri,
    i da doda igru u neku od svojih listi.

    **Srodni pogledi**

    :view:`tabletop.views.update_statistics_view`

    ``Template``

    :template:`game_page.html`

    """

    #nadji igru sa datim nazivom
    igra = Igra.objects.get(naziv=name)
    #dohvati sve recenzije za tu igru
    recenzije = Utisak.objects.filter(idigre=igra.idigre).exclude(statusizmene=STATUS_OBRISAN)

    #za moderatora pronadji odgovarajuce informacije
    statistike = Statistika.objects.filter(idigre=igra)
    dostignuca = Dostignuca.objects.filter(idigre=igra.idigre)
    broj_utisaka = Utisak.objects.filter(
        idigre=igra
    ).exclude(statusizmene=STATUS_OBRISAN).count()

    #napravi string u tacnom formatu za tu igru kako bi query-ovao BGG API
    board_game_bgg_string = "http://boardgamegeek.com/xmlapi/search?search="
    name_split = name.split()
    len_name_split = len(name_split)
    i=0
    for word in name_split:
        board_game_bgg_string += word
        i += 1
        if i < len_name_split:
            board_game_bgg_string += "%20"

    #Sada, potrazi sve igre u BGG koje imaju to ime
    #API Key obscured for push to github, in demonstration was unobscured
    bgg_games = requests.get(board_game_bgg_string, headers={"Authorization": "obscured api key"}) #this gets all the games with that in its name
    #sada pretrazi XML koji si dobio kako bi se nasla specificna igra koja treba
    #treba da se izvadi specifican BGG id za tu igru
    list_bgg_games = xml.etree.ElementTree.fromstring(bgg_games.content) #xmk xpath
    bgg_id = 0
    for items in list_bgg_games.findall('.//boardgame'): #xpath
        if items.find('name').text == name:
            bgg_id = items.attrib['objectid']
            break
    bgg_statistics_string = "https://boardgamegeek.com/xmlapi/boardgame/"+str(bgg_id)
    # sada pozovi API za tacno tu igru
    statistics = requests.get(bgg_statistics_string, headers={"Authorization": "Bearer f1e9f7ca-fc96-40fc-b94d-4cba49a2de52"})
    #print(statistics.text)
    tailored_stats = xml.etree.ElementTree.fromstring(statistics.content)
    extracted_data=[]
    extracted_data_dict = dict()
    #sada izvadi statistike koje nam trebaju - sve sto je vec u tabeli (moze da se proveri protiv)
    #kao i neke additions
    #table - year published, min and max players, Genre
    #additions - description from bgg, playtime, artists and designers, publishers, boardgame honors
    if not tailored_stats.findall('.//error'):
        for items in tailored_stats.findall('.//boardgame'):
            extracted_data.append({
                'year_published': items.find('yearpublished').text}
            )
            extracted_data.append({
                'min_players': items.find('minplayers').text,
            })
            extracted_data.append({
                'max_players': items.find('maxplayers').text
            })
            extracted_data.append({
                'playing_time': items.find('playingtime').text,
            })
            extracted_data.append({
                'description': items.find('description').text
            })
            extracted_data.append({
                'genre':items.findall('boardgamecategory')
            })
            extracted_data.append({
                'artists':items.findall('boardgameartist')
            })
            extracted_data.append({
                'designers': items.findall('boardgamedesigner')
            })
            extracted_data.append({
                'publishers':items.findall('boardgamepublisher')
            })
            extracted_data.append({
                'honors':items.findall('boardgamehonor')
            })
        #sada smo u array extracted_data izvadili xml format za svaku stvar koju smo trazili
        #sada moramo to da formatiramo kako bi moglo da se prikaze na stranici igre u tacnom formatu
        extracted_data_dict = dict()
        for item in extracted_data:
            for key, value in item.items():
                if key not in extracted_data_dict:
                    key_name_list = key.split("_")
                    #ako je key vise od dve reci u xml dolazi u ovom_obliku. Razdvoji lepo.
                    key_value = ""
                    for word in key_name_list:
                        key_value += word.capitalize()
                        key_value += " "
                    if isinstance(value, list):
                        #ako smo izvukli listu, moramo da je formatiramo u pravu listu koja moze da se prikaze
                        value_array = []
                        for val in value:
                            value_array.append(str(val.text))
                        extracted_data_dict[key_value] = value_array
                    else:
                        extracted_data_dict[key_value]=value

    #end of formatting

    #dohvati korisnika koji je ulogovan, ako jeste, kao i liste koji moze da on doda ovu igru u
    if request.user.is_authenticated:
        korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
        # izvadimo liste koje nemaju rezervisano ime za ownership
        user_lists = Listaigara.objects.filter(idkor=korisnik).exclude(nazivliste='Imam').exclude(nazivliste='Igrao').exclude(nazivliste='Wishlist').values('nazivliste').distinct()

    #forma za recenzije ovde
    form = RecenzijaForm()
    if request.user.is_authenticated:
        if request.method == "POST":
            form = RecenzijaForm()
            if "ownership-submit" in request.POST:
                #dodaj u liste Imam, Igrao ili Wishlist -> svaki je veci od drugog u ako je vec u nizoj listi dodaj u visu
                lista = request.POST['pracenje']
                #proveri ako je igra vec u toj listi,, i ako jeste redirect nazad.
                user_list = Listaigara.objects.filter(idkor=korisnik, idigre=igra, nazivliste=lista)
                if user_list.exists():
                    return redirect('igra',igra.naziv)

                #ako nije vec u toj listi, proveri svaku drugu od vlasnistva liste i ako je tu izbaci je
                ima_list = Listaigara.objects.filter(idkor=korisnik, idigre=igra, nazivliste="imam")
                igrao_list = Listaigara.objects.filter(idkor=korisnik, idigre=igra, nazivliste="igrao")
                wish_list = Listaigara.objects.filter(idkor=korisnik, idigre=igra, nazivliste="wishlist")

                if ima_list.exists() and lista != "ima":
                    ima_list.delete()
                if igrao_list.exists() and lista != "igrao":
                    igrao_list.delete()
                if wish_list.exists() and lista != "wishlist":
                    wish_list.delete()

                #na kraju, nadji najveci id u listi i dodaj novo kreiranoj lista object taj id + 1
                highest_key = Listaigara.objects.all()
                if highest_key.exists():
                    highest_key = int(highest_key.latest("idliste").idliste)
                else:
                    highest_key = 0

                Listaigara.objects.create(idliste=highest_key+1, idkor=korisnik, idigre=igra, nazivliste=lista, privatnost=0)

                return render(request, 'korisnik/game_page.html',
                              {'igra': igra, 'utisci': recenzije,
                               'statistics': extracted_data_dict, 'form': form, 'userlists':user_lists,
                               'statistike': statistike,
                                'dostignuca': dostignuca,
                                'broj_utisaka': broj_utisaka,
                                'STATUS_SAKRIVEN': STATUS_SAKRIVEN,
                                'STATUS_FILTRIRAN': STATUS_FILTRIRAN,
                                'korisnik_tip': korisnik.tip,
                                'TIP_MODERATOR': TIP_MODERATOR,
                                'TIP_ADMIN': TIP_ADMIN,})

            elif "recenzija-submit" in request.POST:
                #ostavlja utisak
                form=RecenzijaForm(request.POST)
                if form.is_valid():
                    user=Korisnik.objects.get(korisnickoime=request.user.username)
                    postojeci_utisak = Utisak.objects.filter(idigre=igra, idkor=user)
                    if postojeci_utisak.exists():
                        postojeci_utisak.delete()
                    Utisak.objects.create(idigre=igra, idkor=user,opis=form.cleaned_data['opis']
                    ,ocena=form.cleaned_data['rating'])

            elif "list-submit" in request.POST:
                #naparvi novi lista igra objekat za novo dodatu igru
                if 'liste' in request.POST:
                    highest_key = Listaigara.objects.all().latest("idliste")
                    Listaigara.objects.create(idliste=highest_key.idliste+1, idkor=korisnik, idigre=igra, nazivliste=request.POST['liste'], privatnost=0)
        else:
            form=RecenzijaForm()
    if request.user.is_authenticated:
        #print(korisnik.tip)
        return render(request, 'korisnik/game_page.html',
                  {'igra': igra, 'utisci': recenzije, 'statistics': extracted_data_dict,
                   'form': form, 'userlists':user_lists, 'statistike': statistike,
                    'dostignuca': dostignuca,
                    'broj_utisaka': broj_utisaka,
                    'STATUS_SAKRIVEN': STATUS_SAKRIVEN,
                    'STATUS_FILTRIRAN': STATUS_FILTRIRAN,
                    'korisnik_tip':korisnik.tip,
                    'TIP_MODERATOR': TIP_MODERATOR,
                    'TIP_ADMIN': TIP_ADMIN,
                    })
    else:
        return render(request, 'korisnik/game_page.html',
                      {'igra': igra, 'utisci': recenzije,
                       'statistics': extracted_data_dict,'statistike': statistike,
                        'dostignuca': dostignuca,
                        'broj_utisaka': broj_utisaka,
                        'STATUS_SAKRIVEN': STATUS_SAKRIVEN,
                        'STATUS_FILTRIRAN': STATUS_FILTRIRAN,
                        'TIP_MODERATOR': TIP_MODERATOR,
                        'TIP_ADMIN': TIP_ADMIN,
                        })

@login_required
def profile_view(request):
    """
    **VIEW**

    Pogled na stranicu trenutno ulogovanog korisnika. Kao i za sve korisnike, vadi mu se
    sve javno na stranici vidljive informacije i prikazuje se na njegovoj stranici. Takodje
    mu se prikazuju sva prijatelstva i zahtevi za prijatelstvo na desnoj strani stranice
    i na koje moze da utice (raskine prijatelstvo, prihvati zahtev itd.)

    **Srodni pogledi**

    :view:`tabletop.views.own_statistics_view`

    :view:`tabletop.views.own_game_lists_view`

    :view:`tabletop.views.own_games_view`

    :view:`tabletop.views.own_achievements_view`

    :view:`tabletop.views.profile_settings_view`

    ``Template``

    :template:`korisnik/profile_page.html`

    """
    profil = Korisnik.objects.get(korisnickoime=request.user.username)
    #dohvati sve javne na stranici informacije o korisniku
    #liste
    liste = Listaigara.objects.filter(idkor=profil.idkor, privatnost=3).exclude(nazivliste="Imam").exclude(nazivliste='Igrao').exclude(nazivliste='Wishlist').order_by("nazivliste")
    #vlasnistvo
    ima_list = Listaigara.objects.filter(idkor=profil.idkor, privatnost=3, nazivliste="Imam")
    igrao_list = Listaigara.objects.filter(idkor=profil.idkor, privatnost=3, nazivliste="Igrao")
    wish_list = Listaigara.objects.filter(idkor=profil.idkor, privatnost=3, nazivliste="Wishlist")
    #statistike, koja mora da se anotira sa kojom igrom pripada i naziv statistike
    igre = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0))
    finalne_statistike = []
    for igra in igre:
        statistika = Statistika.objects.filter(idigre=igra.idigre)
        for stat in statistika:
            stat_skup = Vodjenastatistika.objects.filter(idkor=profil.idkor, idigre=igra.idigre,
                                                         idsta=stat.idsta, privatnost=3).annotate(
                nazivigre=Value(igra.naziv)).annotate(nazivstat=Value(stat.naziv))
            if stat_skup.exists():
                stat_skup = stat_skup.latest('datum')
                finalne_statistike.append(stat_skup)
    #dostignuca
    vodjene_statistike = Vodjenastatistika.objects.filter(idkor=profil)
    finalna_dostignuca = []
    for stat in vodjene_statistike:
        dostignuca = Korisnikdostignuca.objects.filter(idvodj=stat.idvodj, privatnost=3)
        if dostignuca.exists():
            for dost in dostignuca:
                finalna_dostignuca.append(dost)

    #dohvati sva prijatelstva, koja moze biti obostrana, i jednostrani zahtevi za prijatelstvo koji korisnik prima
    prijateljstva = Prijatelji.objects.filter(statuszahteva=1, idkor1=profil.idkor) | Prijatelji.objects.filter(statuszahteva=1, idkor2=profil.idkor)
    zahtevi = Prijatelji.objects.filter(statuszahteva=0, idkor2=profil.idkor)
    #sada, za sta korisnik klikne oko prijatelja se promeni (ili obrise) prijateljstvo
    if request.method=="POST":
        if "raskini" in request.POST:
            korisnik = Korisnik.objects.get(korisnickoime=request.POST['raskini'])
            (Prijatelji.objects.filter(idkor2=korisnik,idkor1=profil, statuszahteva=1) | Prijatelji.objects.filter(idkor1=korisnik,idkor2=profil, statuszahteva=1)).delete()
        elif "prihvati" in request.POST:
            korisnik = Korisnik.objects.get(korisnickoime=request.POST['prihvati'])
            Prijatelji.objects.filter(idkor1=korisnik, idkor2=profil).update(statuszahteva=1)
        elif "odbij" in request.POST:
            korisnik = Korisnik.objects.get(korisnickoime=request.POST['odbij'])
            Prijatelji.objects.filter(idkor1=korisnik, idkor2=profil, statuszahteva=0).delete()
    return render(request,'korisnik/profile_page.html', {'korisnik':profil, 'prijateljstva':prijateljstva, 'zahtevi':zahtevi, 'liste':liste, 'imam_liste':ima_list, 'igrao_liste':igrao_list, 'wishlist_list':wish_list, 'statistics':finalne_statistike, 'dostignuca':finalna_dostignuca})

def search_view(request):
    """
    **VIEW**

    Pogled koji se koristi kako bi korisnik mogao da trazi korisnike ili igre pre ko search-bara na
    vrhu stranice u navbaru. Query-uje se korisnicka tabela i tabela igra kako bi se naslo, i ako nema
    posalje se na stranu koja oznacava da se nije ista naslo.

    ``Template``

    :template:`not_found_page.html`

    """
    #ako je korisnik ulogovan, i trazi sebe, posalj ga na svoju stranicu
    if request.user.is_authenticated:
        if request.POST['searchbar']==request.user.username:
            return redirect('profile')
    #ako se nadje igra koja se trazi, posaljii
    igra = Igra.objects.filter(naziv=request.POST['searchbar'])
    if igra.exists():
        return redirect('igra', igra.first().naziv)
    #ako se trazi korisnik koji se trazi, posalji
    korisnik = Korisnik.objects.filter(korisnickoime=request.POST['searchbar'])
    if korisnik.exists():
        return redirect('other-profile',korisnik.first().korisnickoime)
    return render(request, 'korisnik/not_found_page.html', {})

@login_required
def update_statistics_view(request, name):
    """
    **VIEW**

    Pogled koji prikazuje sve statistike igre i gde korisnik moze da ih promeni. Kada korisnik
    pritisne na sacuvaj dugme, sve vrednosti koje su bile upisane u tom trenutku se dodaju
    kao nova vodjena statistika, i prati se da li je korisnik dobio neko dostignuce.

    **Srodni pogledi**

    :view:`tabletop.views.statistic_graphic_view`

    ``Template``

    :template:`update_statistics.html`

    """
    #prvo, dohvati sve statistike za igru
    igra = Igra.objects.get(naziv=name)
    statistike = Statistika.objects.filter(idigre=igra.idigre)

    #kada korisnik promeni neku statistiku i klikne na "Sacuvaj" dugme, onda se pozove ovaj deo
    if request.method == "POST":
        for stat in statistike:
            if request.POST.get(stat.naziv):
                #proveri se svaka statistika za ovu igru i ako je ona promenjena, napravi se nova vodjena statistika
                currtime = datetime.now()
                korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
                if request.POST[stat.naziv]:
                    #ukoliko postoji vec ova statistika u vodjenoj statistici, promeni joj privatnost kako se ne bi videla na stranici korisnika
                    reset_privacy  = Vodjenastatistika.objects.filter(idkor=korisnik, idsta=stat.idsta, idigre=igra.idigre)
                    if reset_privacy.exists():
                        reset_privacy.update(privatnost=0)
                    vodj = Vodjenastatistika.objects.create(idkor=korisnik, idsta=stat.idsta, idigre=igra.idigre, vrednost=request.POST[stat.naziv], datum=currtime, privatnost=0)
                    vrednost = request.POST[stat.naziv]
                    #sa statistike se sada gleda koji tip su, i vadi se njihova vrednost kako bi se uporedila sa dostignucima
                    #za ne numericke tipove, gleda se koliko puta je statistika bilia izabrana na istorickom nivou
                    if stat.tip != "numericka":
                        vrednost = Vodjenastatistika.objects.filter(idkor=korisnik, idsta=stat.idsta, idigre=igra.idigre, vrednost=request.POST[stat.naziv]).count()
                    else:
                        vrednost = int(vrednost)
                    #------------------------------------------------------------------------------------------------- FIX USLOV HERE
                    dostignuca = Dostignuca.objects.filter(idsta=stat.idsta)
                    #Za svako dostignuce za ovu igru, proveri da li je statistika dosla do uslova
                    for dost in dostignuca:
                        #uslov ovde
                        if dost.uslov == ">=":
                            if vrednost >= int(dost.vrednostzadostici):
                                #ako jeste dostigla, proveri se prov ako vec postoji
                                vodjene_za_korisnika = Vodjenastatistika.objects.filter(idkor=korisnik, idsta=stat.idsta)
                                possible_dost = Korisnikdostignuca.objects.none()
                                for vodjena in vodjene_za_korisnika:
                                    possible_dost |= Korisnikdostignuca.objects.filter(idvodj=vodjena, dostignuce=dost)
                                #ako ne postoji vec ovo dostignuce, doda se a suprotnosti se ne dodaje
                                if not possible_dost.exists():
                                    Korisnikdostignuca.objects.create(idvodj=vodj, datum=currtime, privatnost=0, dostignuce=dost)
                        elif dost.uslov == ">":
                            if vrednost > int(dost.vrednostzadostici):
                                #ako jeste dostigla, proveri se prov ako vec postoji
                                vodjene_za_korisnika = Vodjenastatistika.objects.filter(idkor=korisnik, idsta=stat.idsta)
                                possible_dost = Korisnikdostignuca.objects.none()
                                for vodjena in vodjene_za_korisnika:
                                    possible_dost |= Korisnikdostignuca.objects.filter(idvodj=vodjena, dostignuce=dost)
                                #ako ne postoji vec ovo dostignuce, doda se a suprotnosti se ne dodaje
                                if not possible_dost.exists():
                                    Korisnikdostignuca.objects.create(idvodj=vodj, datum=currtime, privatnost=0, dostignuce=dost)
                        elif dost.uslov == "=":
                            if vrednost == int(dost.vrednostzadostici):
                            # ako jeste dostigla, proveri se prov ako vec postoji
                                vodjene_za_korisnika = Vodjenastatistika.objects.filter(idkor=korisnik,
                                                                                        idsta=stat.idsta)
                            possible_dost = Korisnikdostignuca.objects.none()
                            for vodjena in vodjene_za_korisnika:
                                possible_dost |= Korisnikdostignuca.objects.filter(idvodj=vodjena,
                                                                                   dostignuce=dost)
                            # ako ne postoji vec ovo dostignuce, doda se a suprotnosti se ne dodaje
                            if not possible_dost.exists():
                                Korisnikdostignuca.objects.create(idvodj=vodj, datum=currtime, privatnost=0,
                                                                  dostignuce=dost)
                        elif dost.uslov == "<":
                            if vrednost < int(dost.vrednostzadostici):
                                #ako jeste dostigla, proveri se prov ako vec postoji
                                vodjene_za_korisnika = Vodjenastatistika.objects.filter(idkor=korisnik, idsta=stat.idsta)
                                possible_dost = Korisnikdostignuca.objects.none()
                                for vodjena in vodjene_za_korisnika:
                                    possible_dost |= Korisnikdostignuca.objects.filter(idvodj=vodjena, dostignuce=dost)
                                #ako ne postoji vec ovo dostignuce, doda se a suprotnosti se ne dodaje
                                if not possible_dost.exists():
                                    Korisnikdostignuca.objects.create(idvodj=vodj, datum=currtime, privatnost=0, dostignuce=dost)
                        elif dost.uslov == "<=":
                            if vrednost <= int(dost.vrednostzadostici):
                                #ako jeste dostigla, proveri se prov ako vec postoji
                                vodjene_za_korisnika = Vodjenastatistika.objects.filter(idkor=korisnik, idsta=stat.idsta)
                                possible_dost = Korisnikdostignuca.objects.none()
                                for vodjena in vodjene_za_korisnika:
                                    possible_dost |= Korisnikdostignuca.objects.filter(idvodj=vodjena, dostignuce=dost)
                                #ako ne postoji vec ovo dostignuce, doda se a suprotnosti se ne dodaje
                                if not possible_dost.exists():
                                    Korisnikdostignuca.objects.create(idvodj=vodj, datum=currtime, privatnost=0, dostignuce=dost)
                        else:
                            #u slucaju da je nista od toga, pretpostavi default je >=
                            if vrednost >= int(dost.vrednostzadostici):
                                #ako jeste dostigla, proveri se prov ako vec postoji
                                vodjene_za_korisnika = Vodjenastatistika.objects.filter(idkor=korisnik, idsta=stat.idsta)
                                possible_dost = Korisnikdostignuca.objects.none()
                                for vodjena in vodjene_za_korisnika:
                                    possible_dost |= Korisnikdostignuca.objects.filter(idvodj=vodjena, dostignuce=dost)
                                #ako ne postoji vec ovo dostignuce, doda se a suprotnosti se ne dodaje
                                if not possible_dost.exists():
                                    Korisnikdostignuca.objects.create(idvodj=vodj, datum=currtime, privatnost=0, dostignuce=dost)

    return render(request,'korisnik/update_statistic.html', {'statistics':statistike})
@login_required
def own_statistics_view(request):
    """
    **VIEW**

    Pogled koji prikazuje sve statistike koje korisnik prati i za koju igru pripadaju.
    Takodje korisnik ovde moze da izmeni nivo privatnosti specificne statistike

    ``Template``

    :template:`own_statistics.html`

    """
    #nadji sve igre i korisnika
    korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
    igre = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0))
    finalne_statistike = []

    for igra in igre:
        #za svaku statistiku od neke igre, proveri se da li postoji vodjena statistika o njoj
        statistika = Statistika.objects.filter(idigre=igra.idigre)
        for stat in statistika:
            stat_skup = (Vodjenastatistika.objects.filter(idkor=korisnik.idkor, idigre=igra.idigre,
                                                         idsta=stat.idsta).annotate(nazivigre=Value(igra.naziv))
                         .annotate(nazivstat=Value(stat.naziv))) #anotiraj sa nazivom igre
            # ako vodjena statistika postoji, dohvati najnoviju u dodaj je u skup statistika
            if stat_skup.exists():
                stat_skup = stat_skup.latest('datum')
                finalne_statistike.append(stat_skup)

    #ako korisnik klikne da promeni javnost neke igre, ovde izmeni privatnost
    if request.method == "POST":
        privatnost = 0
        if request.POST['javnost'] == "javnostranica":
            privatnost = 3
        elif request.POST['javnost'] == "javno":
            privatnost = 2
        elif request.POST['javnost'] == "prijatelji":
            privatnost = 1
        elif request.POST['javnost'] == "privatno":
            privatnost = 0

        stat = Vodjenastatistika.objects.filter(idvodj = int(request.POST['stat']))
        stat.update(privatnost=privatnost)

    return render(request,'korisnik/own_statistics.html', {'statistics':finalne_statistike})
@login_required
def own_game_lists_view(request):
    """
    **VIEW**

    Pogled koji prikazuje sve liste igara koji je korisnik napravio. Za svaku listu, moze da se
    izbaci specificne igre iz liste, da se napravi nova lista i da se promeni privatnost liste
    igara.

    ``Template``

    :template:`own_game_lists.html`

    """
    #prvo pronadji sve liste igara koje je korisnik naparvio i nisu rezervisane za vlasnistvo
    korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
    liste = Listaigara.objects.filter(idkor=korisnik.idkor).exclude(nazivliste = "Imam").exclude(nazivliste="Igrao").exclude(nazivliste="Wishlist").order_by('nazivliste')

    if request.method == "POST":
        if "list-remove" in request.POST:
            #ako korisnik zahteva da se neka igra izbaci iz liste, dohvati se odgovarajuci element liste i izbaci se
            igra = Igra.objects.get(naziv=request.POST['listaitem'])
            Listaigara.objects.filter(idigre=igra, idkor=korisnik.idkor, nazivliste=request.POST['currlist']).delete()
        elif "privatnost-submit" in request.POST:
            #ovde se menja privatnost svih elemenata liste koji pripadaju korisnickoj listi
            listitems = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste=request.POST['zalistu'])
            if request.POST['javnost'] == "javnostranica":
                listitems.update(privatnost=3)
            elif request.POST['javnost'] == "javno":
                listitems.update(privatnost=2)
            elif request.POST['javnost'] == "prijatelji":
                listitems.update(privatnost=1)
            elif request.POST['javnost'] == "privatno":
                listitems.update(privatnost=0)
        elif "make-list" in request.POST:
            #ako korisnik hoce da napravi novu listu, prvo se proveri da nije uzeo rezervisano ime
            if "Imam" in request.POST['list-name']:
                return redirect('my-game-lists') #check here if redirects work, they do!
            elif "Igrao" in request.POST['list-name']:
                return redirect('my-game-lists')
            elif "Wishlist" in request.POST['list-name']:
                return redirect('my-game-lists')
            #ako nije uzeo rezervisano ime, prvo se proveri da li postoji vec lista po ovim imenom
            existing_list = Listaigara.objects.filter(nazivliste=request.POST['list-name'])
            if existing_list.exists():
                return redirect('my-game-lists')
            #ako ne postoji ova lista vec, naparvi se lista objekat sa prvom igrom u tabeli igara
            #ovo moze da se promeni da prvo dodaje neku dummy igru.
            highest_key = Listaigara.objects.all()
            if highest_key.exists():
                highest_key = int(highest_key.latest("idliste").idliste)
            else:
                highest_key = 0
            Listaigara.objects.create(idliste=highest_key+1, idkor=korisnik, idigre=Igra.objects.all().first(), nazivliste=request.POST['list-name'], privatnost=0)

    return render(request, 'korisnik/own_game_lists.html', {"lists":liste})
@login_required
def own_games_view(request):
    """
    **VIEW**

    Pogled koji prikazuje sve igre koji korisnik ima neko vlasnistvo na. Za individualne igre
    u ovim listama moze da se promeni vidljivost

    ``Template``

    :template:`own_games_page.html`

    """
    #dohvati korisnika i sve liste vlastnistva za tog korisnika, zatim ih spoji u jedno
    korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
    listeImam = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Imam")
    listeIgrao = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Igrao")
    listeWishlist = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Wishlist")

    liste = listeImam.union(listeIgrao.union(listeWishlist))

    if request.method=="POST":
        igra = Igra.objects.get(naziv=request.POST['zaigru'])
        listitem = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste=request.POST['lista'], idigre=igra.idigre)
        #za specificnu igru iz specificne liste vlasnistva, moze da se promeni vidljivost
        if request.POST['javnost'] == "javnostranica":
            listitem.update(privatnost=3)
        elif request.POST['javnost']=="javno":
            listitem.update(privatnost=2)
        elif request.POST['javnost']=="prijatelji":
            listitem.update(privatnost=1)
        elif request.POST['javnost']=="privatno":
            listitem.update(privatnost=0)
    return render(request, 'korisnik/own_games_page.html', {"lists":liste})
@login_required
def own_achievements_view(request):
    """
    **VIEW**

    Pogled koji prikazuje sva dostignuca koji je korisnik postigao sa njihovim slikama.
    Takodje na stranici moze da se promeni privatnost individualnog dostignuca.

    ``Template``

    :template:`own_achievements.html`

    """
    #dohvati sve vodjene statistike od korisnika
    korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
    vodjene_statistike = Vodjenastatistika.objects.filter(idkor=korisnik)
    finalna_dostignuca = []
    for stat in vodjene_statistike:
        # za svaku statistiku, proveri da li postoji srodno dostignuce, i ako jeste dodaj u listu
        #za prikaz
        dostignuca = Korisnikdostignuca.objects.filter(idvodj=stat.idvodj)
        if dostignuca.exists():
            for dost in dostignuca:
                finalna_dostignuca.append(dost)

    if request.method=="POST":
        #za specificno dostignuce moze da se promeni privatnost
        dostig= Korisnikdostignuca.objects.filter(idvodj=request.POST['dost_id'])
        if request.POST['javnost'] == "javnostranica":
            dostig.update(privatnost=3)
        elif request.POST['javnost']=="javno":
            dostig.update(privatnost=2)
        elif request.POST['javnost']=="prijatelji":
            dostig.update(privatnost=1)
        elif request.POST['javnost']=="privatno":
            dostig.update(privatnost=0)
    return render(request, 'korisnik/own_achievements.html',{'dostignuca':finalna_dostignuca} )


def other_user_profile_view(request, username):
    """
    **VIEW**

    Pogled koji prikazuje stranicu korisnika koji je potrazen. Prikazuje svu informaciju kao
    i kod stranice ulogovanog korisnika, sa dodatnom opcijom da se ovaj korisnik dodaje kao prijatelj.

    **Srodni pogledi**

    :view:`tabletop.views.other_user_games_view`
    :view:`tabletop.views.other_user_game_lists_view`
    :view:`tabletop.views.other_user_statistics_view`
    :voew:`tabletop.views.other_user_achievements_view`

    ``Template``

    :template:`user_profile.html`

    """
    korisnik = Korisnik.objects.get(korisnickoime=username)
    if korisnik.obrisan == 1:
        #ne moze da se gleda obrisan korisnik jer ne postoji
        return redirect('igre')
    # Kao i kod ulogovanog korisnika, dohvati svu informaciju koja je vidljiva na stranici
    liste = Listaigara.objects.filter(idkor=korisnik.idkor, privatnost=3).exclude(nazivliste="Imam").exclude(
        nazivliste='Igrao').exclude(nazivliste='Wishlist').order_by("nazivliste")
    ima_list = Listaigara.objects.filter(idkor=korisnik.idkor, privatnost=3, nazivliste="Imam")
    igrao_list = Listaigara.objects.filter(idkor=korisnik.idkor, privatnost=3, nazivliste="Igrao")
    wish_list = Listaigara.objects.filter(idkor=korisnik.idkor, privatnost=3, nazivliste="Wishlist")
    igre = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0))
    finalne_statistike = []
    for igra in igre:
        statistika = Statistika.objects.filter(idigre=igra.idigre)
        for stat in statistika:
            stat_skup = Vodjenastatistika.objects.filter(idkor=korisnik.idkor, idigre=igra.idigre,
                                                         idsta=stat.idsta, privatnost=3).annotate(
                nazivigre=Value(igra.naziv)).annotate(nazivstat=Value(stat.naziv))
            if stat_skup.exists():
                stat_skup = stat_skup.latest('datum')
                finalne_statistike.append(stat_skup)
    vodjene_statistike = Vodjenastatistika.objects.filter(idkor=korisnik)
    finalna_dostignuca = []
    for stat in vodjene_statistike:
        dostignuca = Korisnikdostignuca.objects.filter(idvodj=stat.idvodj, privatnost=3)
        if dostignuca.exists():
            for dost in dostignuca:
                finalna_dostignuca.append(dost)
    # proveri da li prijateljstvo postoji izmedju ulogovanog korisnika i korisnika koji trenutno gledam, jer onda ne moze da
    # se posalje zahtev za prijateljstvo
    prijatelj = False
    if request.user.is_authenticated:
        logged_user = Korisnik.objects.get(korisnickoime=request.user.username)
        prijateljstva = Prijatelji.objects.filter(idkor1=korisnik, idkor2=logged_user) | Prijatelji.objects.filter(idkor1=logged_user, idkor2=korisnik)
        if prijateljstva.exists():
            prijatelj = True
    #ako se klikne na dodavanje prijatelja, posalje se zahtev za prijateljstvo, ili ako vec postoji prijateljstvo redirectuje se
    #ka ovoj stranici
    if request.user.is_authenticated:
        if request.user.username == username:
            return redirect('profile')
        if request.method == "POST":
            user_logged = Korisnik.objects.get(korisnickoime=request.user.username)
            friendships = Prijatelji.objects.filter(idkor2=korisnik, idkor1=user_logged) | Prijatelji.objects.filter(idkor1=korisnik, idkor2=user_logged)
            if friendships.exists():
                return redirect('other-profile')
            Prijatelji.objects.create(idkor2=korisnik, idkor1=user_logged, statuszahteva=0)
    return render(request, 'korisnik/user_profile.html', {"korisnik":korisnik, 'prijatelj':prijatelj, 'liste':liste, 'ima_list':ima_list, 'igrao_list':igrao_list, 'wishlist_list': wish_list, 'statistics': finalne_statistike, 'dostignuca': finalna_dostignuca})

#privacy policy need to check which numbers mean what
def other_user_games_view(request, username):
    """
    **VIEW**

    Pogled koji prikazuje stranicu igara za odgovarajuceg korisnika. Prikazuje isto kao
    i kod ulogovanog korisnika, i proverava se prijateljstvo ulogovanog korisnika i
    pogledanog korisnika jer moze da se dohvati vise informacije.

    ``Template``

    :template:`user_games.html`

    """
    #proveri prijateljstvo jer moze da se dohvati vise informacije ako jesu prijatelji
    korisnik = Korisnik.objects.get(korisnickoime=username)
    if korisnik.obrisan == 1:
        #ne moze da se gleda obrisan korisnik jer ne postoji
        return redirect('igre')

    prijatelj = False
    if request.user.is_authenticated:
        logged_user = Korisnik.objects.get(korisnickoime=request.user.username)
        prijateljstva = Prijatelji.objects.filter(idkor1=korisnik, idkor2=logged_user) | Prijatelji.objects.filter(
            idkor1=logged_user, idkor2=korisnik)
        if prijateljstva.exists():
            prijatelj = True
    listeImam_javnoStranica = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Imam", privatnost=3)
    listeImam_javno = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Imam", privatnost=2)

    listeIgrao_javnoStranica = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Igrao", privatnost=3)
    listeIgrao_javno = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Igrao", privatnost=2)

    listeWishlist_javnoStranica = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Wishlist", privatnost=3)
    listeWishlist_javno =  Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Wishlist", privatnost=2)
    #dohvati sve liste koje su javno sa stranice i generalno jave, i ako je korisnik prijatelj i
    #liste vidljive za prijatelje i spoji ih
    if prijatelj:
        listeImam_prijatelj = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Imam", privatnost=1)
        listeIgrao_prijatelj = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Igrao", privatnost=1)
        listeWishlist_prijatelj = Listaigara.objects.filter(idkor=korisnik.idkor, nazivliste="Wishlist", privatnost=1)

        listeImam = listeImam_javnoStranica.union(listeImam_javno.union(listeImam_prijatelj))
        listeIgrao = listeIgrao_javnoStranica.union(listeIgrao_javno.union(listeIgrao_prijatelj))
        listeWishlist = listeWishlist_javnoStranica.union(listeWishlist_javno.union(listeWishlist_prijatelj))
    else:
        listeImam = listeImam_javnoStranica.union(listeImam_javno)
        listeIgrao = listeIgrao_javnoStranica.union(listeIgrao_javno)
        listeWishlist = listeWishlist_javnoStranica.union(listeWishlist_javno)

    liste = listeImam.union(listeIgrao.union(listeWishlist))

    return render(request, 'korisnik/user_games.html', {"lists": liste, 'korisnik': korisnik})

def other_user_game_lists_view(request, username):
    """
    **VIEW**

    Pogled koji prikazuje stranicu liste igara za odgovarajuceg korisnika. Prikazuje isto kao
    i kod ulogovanog korisnika, i proverava se prijateljstvo ulogovanog korisnika i
    pogledanog korisnika jer moze da se dohvati vise informacije.

    ``Template``

    :template:`user_lists.html`

    """
    #proveri prijateljstvo i dohvati sve liste sa odgovarajucim privatnostima koje nemaju
    #rezervisano ime
    korisnik = Korisnik.objects.get(korisnickoime=username)
    if korisnik.obrisan == 1:
        #ne moze da se gleda obrisan korisnik jer ne postoji
        return redirect('igre')
    prijatelj = False
    if request.user.is_authenticated:
        logged_user = Korisnik.objects.get(korisnickoime=request.user.username)
        prijateljstva = Prijatelji.objects.filter(idkor1=korisnik, idkor2=logged_user) | Prijatelji.objects.filter(
            idkor1=logged_user, idkor2=korisnik)
        if prijateljstva.exists():
            prijatelj = True


    listeJavnoStranica = Listaigara.objects.filter(idkor=korisnik.idkor, privatnost=3).exclude(nazivliste = "Imam").exclude(nazivliste="Igrao").exclude(nazivliste="Wishlist").order_by('nazivliste')
    listeJavno = Listaigara.objects.filter(idkor=korisnik.idkor, privatnost=2).exclude(nazivliste = "Imam").exclude(nazivliste="Igrao").exclude(nazivliste="Wishlist").order_by('nazivliste')
    if prijatelj:
        listePrijatelj = Listaigara.objects.filter(idkor=korisnik.idkor, privatnost=1).exclude(nazivliste="Imam").exclude(
            nazivliste="Igrao").exclude(nazivliste="Wishlist").order_by('nazivliste')
        liste = listeJavnoStranica.union(listeJavno.union(listePrijatelj))
    else:
        liste = listeJavnoStranica.union(listeJavno)

    return render(request, 'korisnik/user_lists.html', {"lists": liste, 'korisnik':korisnik})
def other_user_statistics_view(request, username):
    """
    **VIEW**

    Pogled koji prikazuje stranicu statistike za odgovarajuceg korisnika. Prikazuje isto kao
    i kod ulogovanog korisnika, i proverava se prijateljstvo ulogovanog korisnika i 
    pogledanog korisnika jer moze da se dohvati vise informacije.

    ``Template``

    :template:`user_statistics.html`

    """

    korisnik = Korisnik.objects.get(korisnickoime=username)
    if korisnik.obrisan == 1:
        #ne moze da se gleda obrisan korisnik jer ne postoji
        return redirect('igre')
    #proveri prijateljstvo
    prijatelj = False
    if request.user.is_authenticated:
        logged_user = Korisnik.objects.get(korisnickoime=request.user.username)
        prijateljstva = Prijatelji.objects.filter(idkor1=korisnik, idkor2=logged_user) | Prijatelji.objects.filter(
            idkor1=logged_user, idkor2=korisnik)
        if prijateljstva.exists():
            prijatelj = True

    #itereriraj kroz sve vodjene statistike kao i kod ulogovanog korisnika, sa dodatnom proverom
    #nivoa privatnosti
    igre = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0))
    finalne_statistike = []
    for igra in igre:
        statistika = Statistika.objects.filter(idigre=igra.idigre)
        for stat in statistika:
            stat_skup = Vodjenastatistika.objects.filter(idkor=korisnik.idkor, idigre=igra.idigre,
                                                         idsta=stat.idsta, privatnost=3).annotate(
                nazivigre=Value(igra.naziv)).annotate(nazivstat=Value(stat.naziv))
            if stat_skup.exists():
                stat_skup = stat_skup.latest('datum')
                finalne_statistike.append(stat_skup)
    for igra in igre:
        statistika = Statistika.objects.filter(idigre=igra.idigre)
        for stat in statistika:
            stat_skup = Vodjenastatistika.objects.filter(idkor=korisnik.idkor, idigre=igra.idigre,
                                                         idsta=stat.idsta, privatnost=2).annotate(
                nazivigre=Value(igra.naziv)).annotate(nazivstat=Value(stat.naziv))
            if stat_skup.exists():
                stat_skup = stat_skup.latest('datum')
                finalne_statistike.append(stat_skup)

    if prijatelj:
        for igra in igre:
            statistika = Statistika.objects.filter(idigre=igra.idigre)
            for stat in statistika:
                stat_skup = Vodjenastatistika.objects.filter(idkor=korisnik.idkor, idigre=igra.idigre,
                                                             idsta=stat.idsta, privatnost=1).annotate(
                    nazivigre=Value(igra.naziv)).annotate(nazivstat=Value(stat.naziv))
                if stat_skup.exists():
                    stat_skup = stat_skup.latest('datum')
                    finalne_statistike.append(stat_skup)

    return render(request, 'korisnik/user_statistics.html', {'statistics': finalne_statistike, 'korisnik':korisnik})

def other_user_achievements_view(request, username):
    """
    **VIEW**

    Pogled koji prikazuje stranicu dostignuca za odgovarajuceg korisnika. Prikazuje isto kao
    i kod ulogovanog korisnika, i proverava se prijateljstvo ulogovanog korisnika i
    pogledanog korisnika jer moze da se dohvati vise informacije.

    ``Template``

    :template:`user_games.html`

    """
    korisnik = Korisnik.objects.get(korisnickoime=username)
    if korisnik.obrisan == 1:
        #ne moze da se gleda obrisan korisnik jer ne postoji
        return redirect('igre')
    #proveri prijateljstvo
    prijatelj = False
    if request.user.is_authenticated:
        logged_user = Korisnik.objects.get(korisnickoime=request.user.username)
        prijateljstva = Prijatelji.objects.filter(idkor1=korisnik, idkor2=logged_user) | Prijatelji.objects.filter(
            idkor1=logged_user, idkor2=korisnik)
        if prijateljstva.exists():
            prijatelj = True

    vodjene_statistike = Vodjenastatistika.objects.filter(idkor=korisnik)
    finalna_dostignuca = []
    #za svaku vodjenu statistiku, dohvati ako postoji dostignuce sa odgovarajucim privatnostima
    for stat in vodjene_statistike:
        dostignuca = Korisnikdostignuca.objects.filter(idvodj=stat.idvodj, privatnost=3)
        dostignuca |= Korisnikdostignuca.objects.filter(idvodj=stat.idvodj, privatnost=2)
        if prijatelj:
            dostignuca |= Korisnikdostignuca.objects.filter(idvodj=stat.idvodj, privatnost=1)
        if dostignuca.exists():
            for dost in dostignuca:
                finalna_dostignuca.append(dost)

    return render(request, 'korisnik/user_achievements.html', {'dostignuca': finalna_dostignuca, 'korisnik':korisnik})

@login_required
def statistic_graphic_view(request, id):
    """
    **VIEW**

    Pogled koji prikazuje grafikon napravljen na osnovu odgovarajuce statistike korisnika.
    Koristeci funkcionalnosti Chart.js Javascript biblioteke nekoliko tipa grafikona moze da se prikaze.
    Za numericke tipove podataka, moze da se napravi linearni graph preko vremena sa datumima
    promene statistike kao x-axis, dok za ne numericke tipove moze da se napravi grafikoni
    pie chart i bar chart koji predstavljaju koliko puta na globalnom nivo se izabarala neka vrednost.

    ``Template``

    :template:`graphic_statistic.html`

    """
    #dohvati statistiku i korisnika koji ce se koristiti da se nadje jos informacije za prikaz
    #ovaj deo koristi funkcije Chart.js javascript biblioteke u front delu, i time
    #zahteva podatke i labele za grafikon

    #za numericke tipove, mozemo da napravimo time-line graph koristeci datume sacuvanih vodjenih statistika
    #dok za nenumericke tipove, mozemo da napravimo pie/bar chartove sa globalnim podacima o ponavljanjem
    #odgovarajuceg izbora/teksta.
    statistic_base = Statistika.objects.get(idsta=id)
    korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
    data = []
    labels = []
    type = statistic_base.tipgrafikona
    if statistic_base.tip == "numericka":
        statistike = Vodjenastatistika.objects.filter(idsta=id, idkor=korisnik).order_by('datum')
        for historicalstats in statistike:
            #datum mora da se prebaci u string format kako bi se prikazao kao labela
            labels.append(historicalstats.datum.strftime("%d/%m/%Y"))
            data.append(int(historicalstats.vrednost))
    else:
        statistike = Vodjenastatistika.objects.filter(idsta=id).order_by('vrednost')
        for globalstats in statistike:
            if globalstats.vrednost not in labels:
                labels.append(globalstats.vrednost)
                #za globalne statistike, uzima se vrednost kao broj ponavljana odgovarajuce vrednosti na globalnom nivou
                data.append(Vodjenastatistika.objects.filter(idsta=id, vrednost=globalstats.vrednost).count())

    return render(request, 'korisnik/graphic_statistic.html', {'labels':labels, 'data':data, 'type': type})
@login_required
def profile_settings_view(request):
    """
    **VIEW**

    Pogled koji prikazuje stranicu gde korisnik moze da updatuje svoje podatke. Koristeci form,
    korisnik moze da posalje promenjene podatke koje se proveravaju pre nego sto se ubace u bazu.

    ``Template``

    :template:`profile_settings.html`

    """
    #Napravi korisnicki form koji se prosledji korisniku
    form=KorisnikForm()
    if request.method == "POST":
        #ako korisnik klikne sacuvaj, dohvati korisnika i attachuj njega sa form
        korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
        form=KorisnikForm(request.POST, instance=korisnik)
        if form.is_valid():
            #nemoj odma da sacuvas, nego prvo proveri ako su neke prazne, i ako jesu,
            #nemoj da sacuvas
            obj = form.save(commit=False)
            updated_fields = []
            for field in form.fields:
                # Check if field was submitted empty
                if form.cleaned_data.get(field) in [None, '', []]:
                    # Revert to original database value
                    setattr(obj, field, getattr(form.instance, field))
                else:
                    updated_fields.append(field)
            obj.save(update_fields=updated_fields)

    return render(request, 'korisnik/profile_settings.html', {'form': form})
@login_required
def find_game_for_user_view(request):
    korisnik = Korisnik.objects.get(korisnickoime=request.user.username)
    #closest min and max number of players
    #closest genre
    #several phases of querying
    #query the database for all games - then we are going to parse them to find exact match in player count and genre that isnt
    #the same game, and that the user doesnt already have or has played or wishlisted
    igre = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0))
    ima_lista = Listaigara.objects.filter(idkor=korisnik, nazivliste="Imam")
    igrao_lista = Listaigara.objects.filter(idkor=korisnik, nazivliste="Igrao")
    wish_list = Listaigara.objects.filter(idkor=korisnik, nazivliste="Wishlist")

    #get a queryset of all the games the user has from these 3
    game_list = Igra.objects.none()
    if ima_lista.exists():
        for ima in ima_lista:
            game_list |= Igra.objects.filter(idigre=ima.idigre.idigre)
    if igrao_lista.exists():
        for igrao in igrao_lista:
            game_list |= Igra.objects.filter(idigre=igrao.idigre.idigre)
    if wish_list.exists():
        for wish in wish_list:
            game_list |= Igra.objects.filter(idigre=wish.idigre.idigre)

    #now query to get the average from all the games in this list
    min_broj = 0
    max_broj = 0
    genre = "zabavna" #default we can set for now is like strategy or something
    if game_list.exists():
        min_broj = game_list.aggregate(Avg('minigraca'))
        max_broj = game_list.aggregate(Avg('maxigraca'))

        #for genre, we will count each genre and find the one with the highest count and make that our genre
        top_count = 0
        strategija_count = game_list.filter(zanr='strategija').count()
        if strategija_count > top_count:
            top_count = strategija_count
            genre="strategija"

        porodicna_count = game_list.filter(zanr='porodicna').count()
        if porodicna_count > top_count:
            top_count = porodicna_count
            genre = "porodicna"

        zabavna_count = game_list.filter(zanr='zabavna').count()
        if zabavna_count > top_count:
            top_count = zabavna_count
            genre = "zabavna"

        kooperativna_count = game_list.filter(zanr='kooperativna').count()
        if kooperativna_count > top_count:
            top_count = kooperativna_count
            genre = "kooperativna"

        kartaska_count = game_list.filter(zanr='kartaska').count()
        if kartaska_count > top_count:
            top_count = kartaska_count
            genre = "kartaska"

        apstraktna_count = game_list.filter(zanr='apstraktna').count()
        if apstraktna_count > top_count:
            top_count = apstraktna_count
            genre = "apstraktna"

        tematska_count = game_list.filter(zanr='tematska').count()
        if tematska_count > top_count:
            top_count = tematska_count
            genre = "tematska"

        ratna_count = game_list.filter(zanr='ratna').count()
        if ratna_count > top_count:
            top_count = ratna_count
            genre = "ratna"
    else:
        return redirect('profile')

    #with the 3 aggregate stats now found, we can query the database for something that matches it
    #if cant find it the first time, search only for something in genre, if can't find even that then return to not found
    #if multiple games found as a result, we take the first one ordered by alphabetic order
    hard_correct = Igra.objects.filter(minigraca=min_broj['minigraca__avg'], maxigraca=max_broj['maxigraca__avg'], zanr=genre).exclude(idigre__in=game_list).order_by('naziv')
    soft_correct = Igra.objects.filter(zanr=genre).exclude(idigre__in=game_list).order_by('naziv')
    if hard_correct.exists():
        game_to_return_naziv = hard_correct.first().naziv
        return redirect('igra', name=game_to_return_naziv)
    elif soft_correct.exists():
        game_to_return_naziv = soft_correct.first().naziv
        return redirect('igra', name=game_to_return_naziv)

    return redirect('profile')

#======================================================================== Sofija
# Autor: Sofija Brajovic, 2020/0179
# Opis: Views za registraciju, autentikaciju i gost funkcionalnosti.
#
# Status implementacije:
#   [DONE]  gost_index   - pocetna stranica sa igrama iz baze
#   [DONE]  registracija - validacija i upis novog korisnika u bazu
#   [DONE]  prijava      - autentikacija i sesija
#   [DONE]  odjava       - brisanje sesije

def registracija(request):
    """
    Stranica za registraciju novog korisnika.
    GET:  prikazuje formu za registraciju.
    POST: validira podatke i kreira novi nalog tipa Korisnik, zatim preusmerava na prijavu.
    """
    greska = None

    if request.method == 'POST':
        ime = request.POST.get('ime', '').strip()
        prezime = request.POST.get('prezime', '').strip()
        korisnicko_ime = request.POST.get('korisnicko_ime', '').strip()
        email = request.POST.get('email', '').strip()
        lozinka = request.POST.get('lozinka', '')
        potvrda = request.POST.get('potvrda_lozinke', '')

        if not all([ime, prezime, korisnicko_ime, email, lozinka, potvrda]):
            greska = 'Sva polja su obavezna.'

        elif not validate_pw(lozinka):
            greska = 'Lozinka mora imati min. 8 karaktera, jedno veliko i malo slovo, broj i specijalan znak.'

        elif lozinka != potvrda:
            greska = 'Lozinke se ne poklapaju.'

        elif Korisnik.objects.filter(korisnickoime=korisnicko_ime).exists():
            greska = 'Korisničko ime je zauzeto. Izaberite drugo.'

        elif Korisnik.objects.filter(email=email).exists():
            greska = 'E-mail adresa je već registrovana.'

        else:
            Korisnik.objects.create(
                korisnickoime=korisnicko_ime,
                lozinka=hash_pw(lozinka),
                email=email,
                ime=ime,
                prezime=prezime,
                tip=Korisnik.TIP_KORISNIK,
                privatnost=0,
                datumizmene=timezone.now(),
                obrisan=0,
            )
            #========================================================= Register new user in django
            User.objects.create_user(username=korisnicko_ime, password=lozinka)
            #=========================================================
            return redirect('prijava')

    return render(request, 'autentikacija/registracija.html', {'greska': greska})


def prijava(request):
    """
    Stranica za prijavu korisnika, moderatora i administratora.
    GET:  prikazuje formu za prijavu.
    POST: proverava kredencijale, postavlja sesiju i preusmerava po tipu naloga.
    """
    if 'idkor' in request.session:
        return redirect('igre')

    greska = None

    if request.method == 'POST':
        korisnicko_ime = request.POST.get('korisnicko_ime', '').strip()
        lozinka = request.POST.get('lozinka', '')

        if not korisnicko_ime or not lozinka:
            greska = 'Unesite korisničko ime i lozinku.'
        else:
            lozinka_hash = hash_pw(lozinka)
            try:
                korisnik = Korisnik.objects.get(
                    Q(obrisan__isnull=True) | Q(obrisan=0), #check both
                    korisnickoime=korisnicko_ime,
                    lozinka=lozinka_hash,
                )
                request.session['idkor'] = korisnik.idkor
                request.session['tip'] = korisnik.tip
                request.session['korisnickoime'] = korisnik.korisnickoime
                request.session['ime'] = korisnik.ime
                #================================================ Login user into django system
                user = authenticate(username=korisnicko_ime, password=lozinka)
                if user:
                    login(request,user)
                #=================================================
                return redirect('igre')
            except Korisnik.DoesNotExist:
                greska = 'Pogrešno korisničko ime ili lozinka.'

    return render(request, 'autentikacija/prijava.html', {'greska': greska})

@login_required
def odjava(request):
    """
    Odjavljuje trenutno prijavljenog korisnika brisanjem sesije.
    """
    request.session.flush()
    #============================================================ odjavi iz django aplikacije isto
    logout(request)
    #==========================================================
    return redirect('igre')

#===============================================================================================
#================================================================================ Masa Moderator
#Maša Janković 0462/19
#view funkcije za sve moderatorske stranice
#svaka funkcija odgovara jednoj od url ruta koje su definisane u moderator/urls.py

@moderator_required
def izmena_informacija_igre(request, igra_id):
    """
    prikazuje i obradjuje formu za izmenu informacija o igri

    GET - forma trenutne informacije igre
    POST - validira podatke, cuva izmene i preusmerava na stranicu igre

    template: izmena_informacije_igre.html
    """
    igra = get_object_or_404(
        Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0)),
        idigre = igra_id
    )
    if request.method == 'POST':
        #print(request.POST)
        form = IgraForm(request.POST, instance = igra)
        if form.is_valid():
            igra_obj = form.save(commit = False)
            # cuvamo koji mod je izmenio igru
            #=============================================================== Sacuvamo koristeci tabelu
            moderator = Korisnik.objects.get(korisnickoime=request.user.username)
            igra_obj.promenio = moderator
            #==============================================================
            igra_obj.datumizmene = timezone.now()
            igra_obj.save()
            messages.success(request, 'Informacije o igri su uspešno ažurirane.')
            return redirect('igra',name=igra.naziv)
    else:
        #GET
        form = IgraForm(instance=igra)

    return render(request, 'moderator/izmena_informacija_igre.html', {
        'form': form,
        'igra': igra,
    })

@moderator_required
def pravljenje_statistike(request, igra_id):
    """
    prikazuje i obradjuje formu za kreiranje nove statistike za igru

    GET - prazna forma za unos statistike
    POST - validira, cuva statistiku i preusmerava na stranicu igre

    template: pravljenje_statistike.html
    """

    igra = get_object_or_404(
        Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0)),
        idigre = igra_id
    )

    if request.method == 'POST':
        #print(request.POST)
        form = StatistikaForm(request.POST, igra = igra)
        if form.is_valid():
            statistika = form.save(commit = False)
            #vezujemo statistiku za ovu igru i moderatora koji je kreirao
            statistika.idigre = igra
            # =============================================================== Sacuvamo koristeci tabelu
            moderator = Korisnik.objects.get(korisnickoime=request.user.username)
            statistika.kreirao = moderator
            # ==============================================================
            statistika.datumkreiranja = timezone.now()
            #+=============================================================
            if Statistika.objects.all().exists():
                latest_idsta = Statistika.objects.all().latest('idsta').idsta + 1
                print(latest_idsta)
            else:
                latest_idsta = 1
            statistika.idsta = latest_idsta
            #===============================================================
            statistika.save()
            print("Form is valid")
            messages.success(request, 'Statistika je uspešno kreirana.')
            return redirect('igra', name = igra.naziv)
    else:
        form = StatistikaForm(igra = igra)

    return render(request, 'moderator/pravljenje_statistike.html', {
        'form': form,
        'igra': igra,
    })

@moderator_required
def pravljenje_dostignuca(request, igra_id):
    """
    prikazuje i obradjuje formu za kreiranje novog achievement-a

    GET - prazna forma za unos achievement-a
    POST - validira, cuva achievement i preusmerava na stranicu igre

    template: pravljenje_dostignuca.html
    """
    igra = get_object_or_404(
        Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0)),
        idigre = igra_id
    )
    statistike = Statistika.objects.filter(idigre=igra)

    if request.method == 'POST':
        # igra se prosleđuje da bi filtrirali samo statistike za datu igru
        print(request.POST)
        form = DostignucaForm(request.POST, igra = igra)
        #print(form.fields['idsta'].queryset.query)
        if form.is_valid():
            print("Usao")
            dostignuce = form.save(commit = False)
            dostignuce.idigre = igra.idigre
            # =============================================================== Sacuvamo koristeci tabelu
            moderator = Korisnik.objects.get(korisnickoime=request.user.username)
            dostignuce.kreirao = moderator
            # ==============================================================
            dostignuce.datumkreiranja = timezone.now()
            dostignuce.save()
            messages.success(request, 'Achievement je uspešno kreiran.')
            return redirect('igra', name=igra.naziv)
    else:
        form = DostignucaForm(igra = igra)

    return render(request, 'moderator/pravljenje_dostignuca.html', {
        'form': form,
        'igra': igra,
        'statistike': statistike,
    })

@moderator_required
def upravljanje_utiscima(request, igra_id):
    """
    prikazuje listu utisaka za neku igru sa opcijama za brisanje, filtriranje i skrivanje svakog utiska
    ucitava sve tri forme i prosledjuje ih template-u

    template: upravljanje_utiscima.html

    vraca render sa listom utisaka i formama
    """
    igra = get_object_or_404(
        Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0)),
        idigre = igra_id
    )

    # dohvatamo sve utiske osim obrisanih
    utisci = Utisak.objects.filter(
        idigre=igra
    ).exclude(
        statusizmene=STATUS_OBRISAN
    ).order_by('-datumizmene')

    return render(request, 'moderator/upravljanje_utiscima.html', {
        'igra': igra,
        'utisci': utisci,
        'brisanje_form': UtisakBrisanjeForm(),
        'filtriranje_form': UtisakFiltriranjeForm(),
        'sakrivanje_form': UtisakSakrivanjeForm(),
        'STATUS_AKTIVAN': STATUS_AKTIVAN,
        'STATUS_FILTRIRAN': STATUS_FILTRIRAN,
        'STATUS_SAKRIVEN': STATUS_SAKRIVEN,
    })

@moderator_required
@require_POST
def obrisi_utisak(request):
    """
    AJAX POST - postavlja status utiska na obrisan
    evidentira se u bazi (moderator, razlog, status)
    vraca ok ili greska
    """
    #pronalazimo utisak po id-ju igre i id-ju korisnika
    #print(request.POST)
    igra_id = request.POST.get('igra_id')
    kor_id = request.POST.get('kor_id')
    #utisak = get_object_or_404(Utisak, idigre = igra_id, idkor = kor_id)
    form = UtisakBrisanjeForm(request.POST)
    #===================================== Evidentiran moderator
    moderator = Korisnik.objects.get(korisnickoime=request.user.username)
    #=====================================
    if form.is_valid():
        Utisak.objects.filter(
            idigre = igra_id,
            idkor = kor_id
        ).update(
            statusizmene = STATUS_OBRISAN,
            promenio = moderator,
            datumizmene = timezone.now(),
            razlogizmene = form.cleaned_data['razlog_brisanja']
        )
        return JsonResponse({'status': 'ok', 'poruka': 'Utisak je uspešno obrisan.'})
    else:
        return JsonResponse({'status': 'greska', 'greske': form.errors}, status=400)

@moderator_required
@require_POST
def filtriraj_utisak(request):
    """
    AJAX POST - filtrira reci u utisku
    cuva originalni tekst pre filtriranja, a reci koje filtrira zamenjuje zvezdicama
    vraca ok ili gresku
    """
    #print(request.POST)
    igra_id = request.POST.get('igra_id')
    kor_id = request.POST.get('kor_id')
    utisak = get_object_or_404(Utisak, idigre = igra_id, idkor = kor_id)
    og_opis = utisak.originalniopis if utisak.originalniopis else utisak.opis
    form = UtisakFiltriranjeForm(request.POST)

    # ===================================== Evidentiran moderator
    moderator = Korisnik.objects.get(korisnickoime=request.user.username)
    # =====================================

    if form.is_valid():
        reci = form.cleaned_data['reci_za_filtriranje']
        razlog = form.cleaned_data['razlog_filtriranja']

        #filtriramo tekst, svaku rec zamenjujemo zvezdicama
        filtrirani_tekst = utisak.opis
        if reci:
            for rec in reci.split(','):
                rec = rec.strip()
                if rec:
                    filtrirani_tekst = filtrirani_tekst.replace(rec, '*' * len(rec))

        Utisak.objects.filter(
            idigre = igra_id,
            idkor = kor_id
        ).update(
            opis = filtrirani_tekst,
            originalniopis = og_opis,
            statusizmene = STATUS_FILTRIRAN,
            promenio = moderator,
            datumizmene = timezone.now(),
            razlogizmene = razlog
        )

        return JsonResponse({
            'status': 'ok',
            'poruka': 'Utisak je uspešno filtriran.',
            'filtrirani_tekst': filtrirani_tekst,
        })
    else:
        return JsonResponse({'status': 'greska', 'greske': form.errors}, status=400)

@moderator_required
@require_POST
def sakrij_utisak(request):
    """
    AJAX POST - sakriva tekst utiska
    ocena ostaje vidljiva i utice na prosecnu ocenu igre
    vraca ok ili greska
    """
    #print(request.POST)
    igra_id = request.POST.get('igra_id')
    kor_id = request.POST.get('kor_id')
    #utisak = get_object_or_404(Utisak, idigre = igra_id, idkor = kor_id)
    form = UtisakSakrivanjeForm(request.POST)

    # ===================================== Evidentiran moderator
    moderator = Korisnik.objects.get(korisnickoime=request.user.username)
    # =====================================

    if form.is_valid():
        Utisak.objects.filter(
            idigre = igra_id,
            idkor = kor_id
        ).update(
            statusizmene = STATUS_SAKRIVEN,
            promenio = moderator,
            datumizmene = timezone.now(),
            razlogizmene = form.cleaned_data['razlog_sakrivanja']
        )
        return JsonResponse({'status': 'ok', 'poruka': 'Utisak je uspešno sakriven.'})
    else:
        return JsonResponse({'status': 'greska', 'greske': form.errors}, status=400)

#========================================================================================
#=========================================================== Darko Admin
# Darko Omerovic 2017/0653
# view za sve admin funkcionalnosti
@admin_required
def admin_index(request):
    """
    Početna stranica administratorskog dela aplikacije.
    Omogućava pristup svim administratorskim funkcionalnostima.
    **Template:**

    :template:`templates/admin/admin_index.html`
    """
    broj_igara = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0)).count()

    broj_korisnika = (Korisnik.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0)).exclude(tip=TIP_ADMIN).count())
    trenutni_korisnik = request.trenutni_korisnik

    context = {"trenutni_korisnik": trenutni_korisnik, "broj_igara": broj_igara,
               "broj_korisnika": broj_korisnika, }
    return render(request, "admin/admin_index.html", context)


@admin_required
def admin_games(request):
    """
    Prikazuje stranicu sa svim igrama iz baze(koje nisu flagovane kao obrisane).
    Svaka igra ima pridruzenu opciju(dugme) za brisanje te igre.
    **Template:**

    :template:`templates/admin/admin_games.html`
    """
    igre = Igra.objects.filter(Q(obrisan__isnull=True) | Q(obrisan=0))
    context = {'igre': igre}
    return render(request, 'admin/admin_games.html', context)


@admin_required
def admin_users(request):
    """
    Prikazuje stranicu sa svim korisnicima iz baze(sem admina i obrisanih).
    Svaki korisnik ima pridruzenu opciju(dugme) za brisanje korisnika i opciju(dugme) za promenu info korisnika.
    **Template:**

    :template:`templates/admin/admin_users.html`
    """

    korisnici = Korisnik.objects.filter(obrisan=0).exclude(tip=TIP_ADMIN)
    trenutni_korisnik = request.trenutni_korisnik
    context = {'korisnici': korisnici, "trenutni_korisnik": trenutni_korisnik}
    return render(request, 'admin/admin_users.html', context)


@admin_required
def admin_user_detalji(request, id):
    """
    Prikazuje stranicu pojedinacnog korisnika sa zadatim idijem.
    U zavisnosti od izabrane radnje omogucava brisanje ili promenu podataka.
    **Template:**

    :template:`templates/admin/admin_user_detalji.html`
    """

    korisnik = Korisnik.objects.get(idkor=id)

    if korisnik.tip == TIP_ADMIN:
        return redirect("admin_index")

    show_delete_confirm = request.GET.get("confirm_delete") == "1"
    show_change_form = request.GET.get("change") == "1"

    delete_error = None
    change_error = None
    info_message = None

    if request.method == "POST":
        action = request.POST.get("action")

        # ako je izabrano brisanje
        if action == "delete":
            username_potvrda = request.POST.get("username_potvrda", "").strip()

            # ako je unet korektan username(tj koji se poklapa)
            if username_potvrda == korisnik.korisnickoime:
                korisnik.obrisan = 1
                korisnik.datumizmene = timezone.now()
                korisnik.save(update_fields=["obrisan", "datumizmene"])

                request.session["admin_user_delete_success_id"] = korisnik.idkor
                #============================================================================= Add to django table too
                #add here deletion of user in the User table --- have to use username since tables slightly messed up atm
                #either way usernames are exclusive
                user = User.objects.filter(username=korisnik.korisnickoime)
                user.delete()
                #================================================================================================================
                #================================================================================= Takodje mora da se obrise prijateljstva i utisci
                utisci = Utisak.objects.filter(idkor=korisnik.idkor)
                utisci.delete()
                prijateljstva = Prijatelji.objects.filter(idkor1=korisnik.idkor) | Prijatelji.objects.filter(idkor2=korisnik.idkor)
                prijateljstva.delete()
                #================================================
                return redirect("admin_user_delete_success", id=korisnik.idkor)
            # ako omasi username
            else:
                show_delete_confirm = True
                delete_error = "Netačno korisničko ime. Pokušaj ponovo."

        # ako je izabrana promena
        elif action == "change":
            novo_korisnickoime = request.POST.get("korisnickoime", "").strip()
            nova_lozinka = request.POST.get("lozinka", "").strip()

            show_change_form = True

            # ako username ili password novi nisu uneti
            if not novo_korisnickoime or not nova_lozinka:
                change_error = "Korisničko ime i lozinka su obavezni."

            # ako bude potrebe za nekom username validacijom,menjati
            elif len(novo_korisnickoime) > 30:
                change_error = "Korisničko ime ne sme imati više od 30 karaktera."

            # validacija za pw(podlozno promeni pri dogovoru pravila)
            elif not validate_pw(nova_lozinka):
                change_error = "Lozinka mora imati najmanje 8 karaktera, jedno veliko slovo, jedno malo slovo, jedan broj i jedan specijalan znak."

            elif (novo_korisnickoime == korisnik.korisnickoime and nova_lozinka == korisnik.lozinka):
                show_change_form = True
                change_error = "Uneti podaci su isti kao postojeći. Unesi drugačije podatke ili klikni Odustani."

            else:
                new_pw_hash = hash_pw(nova_lozinka)

                # uneo stare username i pw kao nove
                if (novo_korisnickoime == korisnik.korisnickoime and new_pw_hash == korisnik.lozinka):
                    change_error = "Novo korisnicko ime i lozinka su isti.Uneti drugacije podatke."

                # uneo username vec postojeceg korisnika
                elif Korisnik.objects.filter(korisnickoime=novo_korisnickoime).exclude(idkor=korisnik.idkor).exists():
                    change_error = "Korisničko ime već postoji."

                # sve korektno
                else:
                    #====================================================================update django table too
                    user = User.objects.get(username=korisnik.korisnickoime)
                    user.username = novo_korisnickoime
                    user.set_password(nova_lozinka)
                    user.save()
                    #==========================================================================================================
                    korisnik.korisnickoime = novo_korisnickoime


                    korisnik.lozinka = new_pw_hash
                    korisnik.datumizmene = timezone.now()

                    korisnik.save(update_fields=["korisnickoime", "lozinka", "datumizmene"])
                    request.session["admin_user_change_success_id"] = korisnik.idkor

                    return redirect("admin_user_change_success", id=korisnik.idkor)

    context = {"korisnik": korisnik, "show_delete_confirm": show_delete_confirm, "show_change_form": show_change_form,
               "delete_error": delete_error, "change_error": change_error, "info_message": info_message, }
    return render(request, "admin/admin_user_detalji.html", context)


@admin_required
@require_GET
def admin_user_delete_success(request, id):
    """
    Stranica potvrde brisanja izabranog korisnika.
    Postoji dugme za vracanje na admin_user.
    **Template:**

    :template:`templates/admin/admin_user_delete_success.html`
    """
    # guard da ne moze rendom da uleti na url za delete_success
    dozvoljeni_id = request.session.pop("admin_user_delete_success_id", None)

    if dozvoljeni_id != id:
        return redirect("admin_users")
    korisnik = Korisnik.objects.get(idkor=id)

    context = {"korisnik": korisnik}
    return render(request, "admin/admin_user_delete_success.html", context)


@admin_required
@require_GET
def admin_user_change_success(request, id):
    """
    Stranica potvrde promene kredencijala izabranog korisnika.
    Postoji dugme za vracanje na admin_user.
    **Template:**

    :template:`templates/admin/admin_user_change_success.html`
    """
    # guard da ne moze rendom da uleti na url za change_success
    dozvoljeni_id = request.session.pop("admin_user_change_success_id", None)

    if dozvoljeni_id != id:
        return redirect("admin_users")

    korisnik = Korisnik.objects.get(idkor=id)
    context = {"korisnik": korisnik}
    return render(request, "admin/admin_user_change_success.html", context)


@admin_required
def admin_game_detalji(request, id):
    """
    Prikazuje stranicu pojedinacne igre sa zadatim idijem.
    Omogucava brisanje date igre.
    **Template:**

    :template:`templates/admin/admin_user_detalji.html`
    """
    igra = Igra.objects.get(idigre=id)

    show_delete_confirm = request.GET.get("confirm_delete") == "1"
    delete_error = None

    if request.method == "POST":
        naziv_potvrda = request.POST.get("naziv_potvrda", "").strip()

        if naziv_potvrda == igra.naziv:
            igra.obrisan = 1
            igra.save(update_fields=["obrisan"])

            request.session["admin_game_delete_success_id"] = igra.idigre

            return redirect("admin_game_delete_success", id=igra.idigre)

        else:
            show_delete_confirm = True
            delete_error = "Netacan naziv igre.Pokusaj ponovo"
    context = {"igra": igra, "show_delete_confirm": show_delete_confirm, "delete_error": delete_error}
    return render(request, "admin/admin_game_detalji.html", context)


@admin_required
@require_GET
def admin_game_delete_success(request, id):
    """
    Stranica potvrde brisanja izabrane igre.
    Postoji dugme za vracanje na admin_games.
    **Template:**

    :template:`templates/admin/admin_game_delete_success.html`
    """
    # guard da ne moze rendom da uleti na url za delete_success
    dozvoljeni_id = request.session.pop("admin_game_delete_success_id", None)

    if dozvoljeni_id != id:
        return redirect("admin_games")

    igra = Igra.objects.get(idigre=id)

    context = {"igra": igra}

    return render(request, "admin/admin_game_delete_success.html", context)
#============================================== END ====================================================================================
