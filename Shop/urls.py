
"""
URLs de l'application shop (e-commerce)
"""

from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Pages publiques
    path('', views.accueil, name='accueil'),
    path('produits/', views.liste_produits, name='liste_produits'),
    path('produit/<int:produit_id>/', views.detail_produit, name='detail_produit'),
    path('categorie/<int:categorie_id>/', views.produits_par_categorie, name='produits_par_categorie'),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_user,name ="logout"),
    
    # Pages informatives
    path('a-propos/', views.a_propos, name='a_propos'),
    path('contact/', views.contact, name='contact'),
    path('methodes-culture/', views.methodes_culture, name='methodes_culture'),
    
    # Panier (authentification requise)
    path('panier/', views.voir_panier, name='voir_panier'),
    path('ajouter-au-panier/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('modifier-panier/<int:ligne_id>/', views.modifier_panier, name='modifier_panier'),
    path('supprimer-du-panier/<int:ligne_id>/', views.supprimer_du_panier, name='supprimer_du_panier'),
    path('vider-panier/', views.vider_panier, name='vider_panier'),
    
    # Commandes (authentification requise)
    path('commander/', views.passer_commande, name='passer_commande'),
    path('confirmation/<int:commande_id>/', views.confirmation_commande, name='confirmation_commande'),
    path('mes-commandes/', views.mes_commandes, name='mes_commandes'),
    path('commande/<int:commande_id>/', views.detail_commande, name='detail_commande'),
    path('annuler-commande/<int:commande_id>/', views.annuler_commande, name='annuler_commande'),
    
    # API AJAX (optionnel)
    path('api/ajouter-panier/', views.api_ajouter_panier, name='api_ajouter_panier'),
    path('api/panier-count/', views.api_panier_count, name='api_panier_count'),
    
    # Callback paiement Mobile Money
    path('api/paiement/callback/', views.paiement_callback, name='paiement_callback'),
]
