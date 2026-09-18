#Darko Omerovic 2017/0653 + Masa
#dekorator za verifikaciju sesije admina
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .models import Korisnik

def moderator_required(view_func):
    #proverava da li je korisnik moderator, tako sto proverava da li je tip=2
    #ako korisnik nije moderator preusmerava na pocetnu stranicu
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            #pronalazimo korisnika na osnovu id i proveravamo tip
            #print(request.user.id)#request user id gets it from requests which arent actually synced
            #for now lets replace id with username------------------------------------------------!
            idkor = request.session.get("idkor")
            # prijava placeholder za pravu login stranicu
            if idkor is None:
                return redirect("prijava")
            korisnik = Korisnik.objects.filter(idkor=idkor)
            if not korisnik.exists():
                return redirect("prijava")
            #print(korisnik)
            korisnik = korisnik.first()
            #print(korisnik.tip)
            if korisnik.tip < 2:
                messages.error(request, 'Nemate dozvolu pristupa ovoj stranici.')
                return redirect('igre')
            #cuvamo korisnik objekat za kasniju upotrebu u viewu
            request.korisnik = korisnik
        except Korisnik.DoesNotExist:
            messages.error(request, 'Korisnik nije pronađen.')
            return redirect('igre')
        return view_func(request, *args, **kwargs)
    return wrapper

TIP_ADMIN = 3

def admin_required(view_function):
    """
    Dekorater za overu sesije i cekiranja da li je trenutni user admin.
    Koristi se kao guard za svaku funkcionalnost admina koju samo on ima.
    """
    @login_required
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):
        idkor = request.session.get("idkor")
        #prijava placeholder za pravu login stranicu
        if idkor is None:
            return redirect("prijava")

        try:
            trenutni_korisnik = Korisnik.objects.get(
                idkor=idkor,
                obrisan=0
            )
        except Korisnik.DoesNotExist:
            request.session.flush()
            return redirect("prijava")

        if trenutni_korisnik.tip != TIP_ADMIN:
            messages.error(request, 'Nemate dozvolu pristupa ovoj stranici.')
            return redirect('igre')

        request.trenutni_korisnik = trenutni_korisnik

        return view_function(request, *args, **kwargs)

    return wrapper