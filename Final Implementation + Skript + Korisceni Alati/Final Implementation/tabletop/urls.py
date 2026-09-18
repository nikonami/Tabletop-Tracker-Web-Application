#Nikola Stamenkovic 2020/0723
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('igre/', views.game_front_page_view, name='igre'),
    path('igra/<str:name>/', views.game_page_view, name='igra'),
    path('profile/', views.profile_view, name='profile'),
    path('search/', views.search_view, name='search'),
    path('igra/statistika/<str:name>/', views.update_statistics_view, name='statistics'),
    path('profile/statistika/', views.own_statistics_view, name='my-statistics'),
    path('profile/liste-igara/', views.own_game_lists_view, name='my-game-lists'),
    path('profile/igre/', views.own_games_view, name='my-games'),
    path('profile/achievements/', views.own_achievements_view, name='my-achievements'),
    path('profile/find-game/', views.find_game_for_user_view, name='find-game'),
    path('profile/profile-settings/', views.profile_settings_view, name='profile-settings'),
    path('profile/<str:username>/', views.other_user_profile_view, name='other-profile'),
    path('profile/<str:username>/igre', views.other_user_games_view, name='other-profile-games'),
    path('profile/<str:username>/liste-igara/', views.other_user_game_lists_view, name='other-profile-game-lists'),
    path('profile/<str:username>/statistics/', views.other_user_statistics_view, name='other-profile-statistics'),
    path('profile/<str:username>/achievements/', views.other_user_achievements_view, name='other-profile-achievements'),
    path('igra/statistika/<int:id>', views.statistic_graphic_view, name='stat-graph'),
    #==============================================================================Sofija
    path('', RedirectView.as_view(url='igre/'), name='glavna-redirect'),
    path('registracija/', views.registracija, name='registracija'),
    path('prijava/', views.prijava, name='prijava'),
    path('odjava/', views.odjava, name='odjava'),
    #====================================================================================
    #=============================================================================== Masa
    # forma za izmenu informacija o igri
    path('moderator/igra/<int:igra_id>/izmeni/', views.izmena_informacija_igre, name='izmena_igre'),

    # forma za pravljenje statistike
    path('moderator/igra/<int:igra_id>/statistika/nova/', views.pravljenje_statistike, name='nova_statistika'),

    # forma za pravljenje achievement-a
    path('moderator/igra/<int:igra_id>/achievement/novi/', views.pravljenje_dostignuca, name='novo_dostignuce'),

    # stranica za upravljanje utiscima
    path('moderator/igra/<int:igra_id>/utisci/', views.upravljanje_utiscima, name='upravljanje_utiscima'),

    # AJAX rute za utiske
    # brisanje utiska
    path('utisak/obrisi/', views.obrisi_utisak, name='obrisi_utisak'),
    # filtriranje reci u utisku
    path('utisak/filtriraj/', views.filtriraj_utisak, name='filtriraj_utisak'),
    # sakrivanje teksta utiska
    path('utisak/sakrij/', views.sakrij_utisak, name='sakrij_utisak'),
    #=========================================================================================
    #================================================================================= Darko
    path('admin_index/',views.admin_index,name='admin_index'),
    path('admin_games/',views.admin_games,name='admin_games'),
    path('admin_users/',views.admin_users,name='admin_users'),
    path('admin_users/user/<int:id>/', views.admin_user_detalji, name='admin_user_detalji'),
    path('admin_games/<int:id>/', views.admin_game_detalji, name="admin_game_detalji"),
    path('admin_games/<int:id>/delete_success/', views.admin_game_delete_success, name="admin_game_delete_success"),
    path('admin_users/user/<int:id>/delete_success/',views.admin_user_delete_success,name="admin_user_delete_success"),
    path('admin_users/user/<int:id>/change_success/',views.admin_user_change_success,name="admin_user_change_success"),
]