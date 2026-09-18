from django.contrib import admin

from tabletop.models import *


# Register your models here.
class DostignucaAdmin(admin.ModelAdmin):
    list_display = ('iddos','naziv', 'uslov', 'vrednostzadostici', 'idigre', 'idsta', 'kreirao', 'datumkreiranja', 'slikaurl')
    list_filter = ('naziv', 'idigre', 'idsta', 'vrednostzadostici')
    search_fields = ('naziv', 'idigre', 'idsta')
    ordering = ('iddos', 'naziv', 'idsta',)

admin.site.register(Dostignuca, DostignucaAdmin)

class IgraAdmin(admin.ModelAdmin):
    list_display = ('idigre', 'naziv', 'opis', 'minigraca', 'maxigraca', 'godinaproizvodnje', 'zanr', 'slikaurl', 'videotutorialurl',
                    'obrisan', 'promenio', 'datumizmene')
    list_filter= ('naziv', 'minigraca', 'maxigraca', 'godinaproizvodnje')
    search_fields = ('naziv', 'zanr')
    ordering = ('idigre', 'naziv', 'minigraca', 'maxigraca', 'godinaproizvodnje')

admin.site.register(Igra, IgraAdmin)

class KorisnikAdmin(admin.ModelAdmin):
    list_display = ('idkor', 'korisnickoime', 'lozinka', 'email', 'tip', 'ime', 'prezime',
                    'obrisan', 'promenio', 'datumizmene')
    list_filter = ('korisnickoime', 'email', 'tip')
    search_fields = ('korisnickoime', 'email')
    ordering = ('idkor', 'korisnickoime', 'tip',)

admin.site.register(Korisnik, KorisnikAdmin)

class KorisnikdostignucaAdmin(admin.ModelAdmin):
    list_display = ('idvodj', 'dostignuce', 'privatnost', 'datum')
    list_filter = ('idvodj', 'dostignuce', 'datum', 'privatnost')
    search_fields = ('idvodj', 'dostignuce')
    ordering =('idvodj', 'dostignuce', 'datum', 'privatnost',)

admin.site.register(Korisnikdostignuca, KorisnikdostignucaAdmin)

#class ListaigaraAdmin(admin.ModelAdmin):
#    list_display = ('idliste', 'idkor', 'idigre', 'nazivliste', 'privatnost')
#    list_filter = ('idliste', 'idkor', 'idigre', 'nazivliste')
#    search_fields = ('idliste')
#    ordering = ('idliste', 'idkor', 'idigre', 'nazivliste',)

#admin.site.register(Listaigara, ListaigaraAdmin)

#class PrijateljiAdmin(admin.ModelAdmin):
#    list_display = ('idkor2', 'idkor1', 'statuszahteva')
#    list_filter = ('idkor2', 'idkor1', 'statuszahteva')
#    search_fields = ('idkor2', 'idkor1')
#    ordering = ('idkor2', 'idkor1', 'statuszahteva',)

#admin.site.register(Prijatelji,PrijateljiAdmin)

#class StatistikaAdmin(admin.ModelAdmin):
#    list_display = ('idsta', 'idigre', 'naziv', 'opis', 'tip', 'dropdown', 'kreirao', 'datumkreiranja')
#    list_filter = ('idsta', 'idigre', 'tip')
#    search_fields = ('idsta', 'idigre', 'naziv', 'opis', 'tip')
#    ordering = ('idsta', 'idigre',)

#admin.site.register(Statistika,StatistikaAdmin)

#class UtisakAdmin(admin.ModelAdmin):
#   list_display = ('idigre', 'idkor', 'opis', 'ocena', 'promenio', 'razlogizmene', 'statusizmene', 'datumizmene')
#    list_filter = ('idigre', 'idkor', 'ocena', 'promenio', 'statusizmene')
#    search_fields = ('idigre', 'idkor', 'ocena', 'promenio', 'razlogizmene', 'statusizmene')
#    ordering = ('idigre', 'idkor', 'ocena',)

#admin.site.register(Utisak, UtisakAdmin)

class VodjenastatistikaAdmin(admin.ModelAdmin):
    list_display = ('idvodj', 'idigre', 'idsta', 'datum', 'tekst', 'vrednost', 'privatnost')
    list_filter = ('idvodj', 'idigre', 'idsta')
    search_fields = ('idvodj', 'idigre','idsta', 'datum')
    ordering = ('idvodj', 'idigre', 'idsta', 'datum',)

admin.site.register(Vodjenastatistika, VodjenastatistikaAdmin)


