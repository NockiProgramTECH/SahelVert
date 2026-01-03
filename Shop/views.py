
# ========== views.py - Vues et logique métier ==========

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import (
    Produit, Categorie, Panier, LignePanier, 
    Commande, LigneCommande, Client, TransactionMobileMoney
)


#views pour la creation de compte  
from django.contrib.auth import login,logout
from .forms import RegisterForm

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # connecte automatiquement après inscription
            return redirect('shop:accueil')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect("shop:accueil")












def accueil(request):
    """
    Page d'accueil du site SahelVert
    Affiche les produits en promotion et nouveautés
    """
    produits_promotion = Produit.objects.filter(
        actif=True,
        stock__gt=0
    )[:8]
    
    nouveautes = Produit.objects.filter(
        actif=True,
        stock__gt=0,
        par_commande =False
    ).order_by('-date_creation')[:8]
    
    categories = Categorie.objects.filter(actif=True)

    
    context = {
        'produits_promotion': produits_promotion,
        'nouveautes': nouveautes,
        'categories': categories,
 
    }
    return render(request, 'shop/index.html', context)


def liste_produits(request):
    """
    Liste tous les produits avec filtres et recherche
    """
    produits = Produit.objects.filter(actif=True)
    
    # Filtre par catégorie
    categorie_id = request.GET.get('categorie')
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)
    
    # Recherche
    recherche = request.GET.get('q')
    if recherche:
        produits = produits.filter(
            Q(nom__icontains=recherche) | 
            Q(description__icontains=recherche)
        )
    
    # Tri
    tri = request.GET.get('tri', 'recent')
    if tri == 'prix_asc':
        produits = produits.order_by('prix')
    elif tri == 'prix_desc':
        produits = produits.order_by('-prix')
    elif tri == 'nom':
        produits = produits.order_by('nom')
    else:
        produits = produits.order_by('-date_creation')
    
    # Pagination
    paginator = Paginator(produits, 12)
    page = request.GET.get('page')
    produits_page = paginator.get_page(page)
    
    categories = Categorie.objects.filter(actif=True)
    
    context = {
        'produits': produits_page,
        'categories': categories,
        'categorie_selectionnee': categorie_id,
        'recherche': recherche,
        'tri': tri,
    }
    return render(request, 'shop/liste_produits.html', context)


def detail_produit(request, produit_id):
    """
    Affiche les détails d'un produit
    """
    produit = get_object_or_404(Produit, id=produit_id, actif=True)
    
    # Avis approuvés
    avis = produit.avis.filter(approuve=True).order_by('-date_creation')
    note_moyenne = avis.aggregate(Avg('note'))['note__avg']
    
    # Produits similaires
    produits_similaires = Produit.objects.filter(
        categorie=produit.categorie,
        actif=True
    ).exclude(id=produit.id)[:4]
    
    context = {
        'produit': produit,
        'avis': avis,
        'note_moyenne': note_moyenne,
        'produits_similaires': produits_similaires,
    }
    return render(request, 'shop/detail_produit.html', context)


@login_required
def ajouter_au_panier(request, produit_id):
    """
    Ajoute un produit au panier du client
    """
    produit = get_object_or_404(Produit, id=produit_id)
    quantite = float(request.POST.get('quantite', 1))
    
    # Vérifier le stock
    if quantite > produit.stock:
        messages.error(request, 'Stock insuffisant')
        return redirect('detail_produit', produit_id=produit_id)
    
    # Récupérer ou créer le client
    client, created = Client.objects.get_or_create(user=request.user)
    
    # Récupérer ou créer le panier
    panier, created = Panier.objects.get_or_create(client=client)
    
    # Ajouter ou mettre à jour la ligne du panier
    ligne_panier, created = LignePanier.objects.get_or_create(
        panier=panier,
        produit=produit,
        defaults={'quantite': quantite}
    )
    
    if not created:
        ligne_panier.quantite += quantite
        ligne_panier.save()
    
    messages.success(request, f'{produit.nom} ajouté au panier')
    return redirect('shop:voir_panier')


@login_required
def voir_panier(request):
    """
    Affiche le panier du client
    """
    try:
        client = Client.objects.get(user=request.user)
        panier = Panier.objects.get(client=client)
        lignes = panier.items.all()
        total = panier.total()
    except (Client.DoesNotExist, Panier.DoesNotExist):
        lignes = []
        total = 0
    
    context = {
        'lignes': lignes,
        'total': total,
    }
    return render(request, 'shop/panier.html', context)


@login_required
def passer_commande(request):
    """
    Finalise la commande à partir du panier
    """
    client = get_object_or_404(Client, user=request.user)
    panier = get_object_or_404(Panier, client=client)
    
    if request.method == 'POST':
        # Créer la commande
        commande = Commande.objects.create(
            client=client,
            adresse_livraison=request.POST.get('adresse'),
            ville_livraison=request.POST.get('ville'),
            quartier_livraison=request.POST.get('quartier'),
            telephone_livraison=request.POST.get('telephone'),
            mode_paiement=request.POST.get('mode_paiement'),
            frais_livraison=1000,  # Frais fixes
            notes_client=request.POST.get('notes', '')
        )
        
        # Créer les lignes de commande
        for ligne_panier in panier.items.all():
            LigneCommande.objects.create(
                commande=commande,
                produit=ligne_panier.produit,
                quantite=ligne_panier.quantite
            )
            
            # Mettre à jour le stock
            produit = ligne_panier.produit
            produit.stock -= ligne_panier.quantite
            produit.save()
        
        # Calculer le total
        commande.calculer_total()
        
        # Vider le panier
        panier.items.all().delete()
        
        messages.success(
            request, 
            f'Commande {commande.numero_commande} confirmée !'
        )
        return redirect('confirmation_commande', commande_id=commande.id)
    
    return render(request, 'shop/checkout.html', {'panier': panier})






# ========== views.py (Extension) - Gestion des paiements ==========

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Paiement, Commande, Client

@login_required
def passer_commande(request):
    """
    Finalise la commande avec création du paiement
    """
    client = get_object_or_404(Client, user=request.user)
    panier = get_object_or_404(Panier, client=client)
    
    if not panier.items.exists():
        messages.error(request, 'Votre panier est vide')
        return redirect('shop:voir_panier')
    
    if request.method == 'POST':
        # Créer la commande
        commande = Commande.objects.create(
            client=client,
            adresse_livraison=request.POST.get('adresse'),
            ville_livraison=request.POST.get('ville'),
            quartier_livraison=request.POST.get('quartier'),
            telephone_livraison=request.POST.get('telephone'),
            mode_paiement=request.POST.get('mode_paiement'),
            frais_livraison=1000,
            notes_client=request.POST.get('notes', '')
        )
        
        # Créer les lignes de commande
        for ligne_panier in panier.items.all():
            LigneCommande.objects.create(
                commande=commande,
                produit=ligne_panier.produit,
                quantite=ligne_panier.quantite
            )
            
            # Mettre à jour le stock
            produit = ligne_panier.produit
            produit.stock -= ligne_panier.quantite
            produit.save()
        
        # Calculer le total
        commande.calculer_total()
        
        # Créer le paiement
        paiement = Paiement.objects.create(
            commande=commande,
            montant=commande.total,
            mode_paiement=request.POST.get('mode_paiement'),
            numero_telephone=request.POST.get('telephone_paiement', '')
        )
        
        # Initier le paiement si Mobile Money
        if paiement.mode_paiement in ['orange_money', 'moov_money']:
            paiement.initier_paiement()
            messages.info(
                request,
                'Un SMS vous a été envoyé pour valider le paiement'
            )
        
        # Vider le panier
        panier.items.all().delete()
        
        return redirect('shop:confirmation_commande', commande_id=commande.id)
    
    return render(request, 'shop/checkout.html', {'panier': panier})


@login_required
def confirmation_commande(request, commande_id):
    """
    Page de confirmation de commande
    """
    commande = get_object_or_404(
        Commande, 
        id=commande_id, 
        client__user=request.user
    )
    
    return render(request, 'shop/confirmation.html', {
        'commande': commande
    })



# ========== views.py (Extension Complète) - Gestion du panier ==========

"""
Vues supplémentaires pour la gestion du panier d'achat
et des commandes
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import (
    Produit, Client, Panier, LignePanier, 
    Commande, LigneCommande, Paiement
)

@login_required
def modifier_panier(request, ligne_id):
    """
    Modifie la quantité d'un produit dans le panier
    """
    ligne = get_object_or_404(LignePanier, id=ligne_id)
    
    # Vérifier que la ligne appartient au panier de l'utilisateur
    if ligne.panier.client.user != request.user:
        messages.error(request, 'Action non autorisée')
        return redirect('voir_panier')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'augmenter':
            # Vérifier le stock disponible
            if ligne.quantite + 0.5 <= ligne.produit.stock:
                ligne.quantite += 0.5
                ligne.save()
                messages.success(request, 'Quantité augmentée')
            else:
                messages.warning(request, 'Stock insuffisant')
        
        elif action == 'diminuer':
            if ligne.quantite > 0.5:
                ligne.quantite -= 0.5
                ligne.save()
                messages.success(request, 'Quantité diminuée')
            else:
                ligne.delete()
                messages.info(request, 'Produit retiré du panier')
    
    return redirect('shop:voir_panier')


@login_required
def supprimer_du_panier(request, ligne_id):
    """
    Supprime un produit du panier
    """
    ligne = get_object_or_404(LignePanier, id=ligne_id)
    
    # Vérifier que la ligne appartient au panier de l'utilisateur
    if ligne.panier.client.user != request.user:
        messages.error(request, 'Action non autorisée')
        return redirect('voir_panier')
    
    if request.method == 'POST':
        produit_nom = ligne.produit.nom
        ligne.delete()
        messages.success(request, f'{produit_nom} retiré du panier')
    
    return redirect('shop:voir_panier')


@login_required
def vider_panier(request):
    """
    Vide complètement le panier
    """
    try:
        client = Client.objects.get(user=request.user)
        panier = Panier.objects.get(client=client)
        
        if request.method == 'POST':
            panier.items.all().delete()
            messages.success(request, 'Panier vidé avec succès')
    except (Client.DoesNotExist, Panier.DoesNotExist):
        pass
    
    return redirect('shop:voir_panier')


@login_required
def mes_commandes(request):
    """
    Liste des commandes du client
    """
    try:
        client = Client.objects.get(user=request.user)
        commandes = Commande.objects.filter(client=client).order_by('-date_commande')
    except Client.DoesNotExist:
        commandes = []
    
    context = {
        'commandes': commandes
    }
    return render(request, 'shop/mes_commandes.html', context)


@login_required
def detail_commande(request, commande_id):
    """
    Détail d'une commande spécifique
    """
    commande = get_object_or_404(
        Commande, 
        id=commande_id,
        client__user=request.user
    )
    
    context = {
        'commande': commande
    }
    return render(request, 'shop/detail_commande.html', context)


@login_required
def annuler_commande(request, commande_id):
    """
    Annule une commande (seulement si elle est en attente)
    """
    commande = get_object_or_404(
        Commande, 
        id=commande_id,
        client__user=request.user
    )
    
    if request.method == 'POST':
        if commande.statut in ['en_attente', 'confirmee']:
            # Remettre les produits en stock
            for item in commande.items.all():
                produit = item.produit
                produit.stock += item.quantite
                produit.save()
            
            # Annuler la commande
            commande.statut = 'annulee'
            commande.save()
            
            # Annuler le paiement si existant
            if hasattr(commande, 'paiement'):
                commande.paiement.statut = 'annule'
                commande.paiement.save()
            
            messages.success(
                request, 
                f'Commande {commande.numero_commande} annulée'
            )
        else:
            messages.error(
                request, 
                'Cette commande ne peut plus être annulée'
            )
    
    return redirect('shop:mes_commandes')


# ========== API pour AJAX (optionnel) ==========

@login_required
def api_ajouter_panier(request):
    """
    API JSON pour ajouter un produit au panier (AJAX)
    """
    if request.method == 'POST':
        produit_id = request.POST.get('produit_id')
        quantite = float(request.POST.get('quantite', 1))
        
        try:
            produit = Produit.objects.get(id=produit_id, actif=True)
            
            # Vérifier le stock
            if quantite > produit.stock:
                return JsonResponse({
                    'success': False,
                    'message': 'Stock insuffisant'
                }, status=400)
            
            # Récupérer ou créer le client et le panier
            client, _ = Client.objects.get_or_create(user=request.user)
            panier, _ = Panier.objects.get_or_create(client=client)
            
            # Ajouter au panier
            ligne, created = LignePanier.objects.get_or_create(
                panier=panier,
                produit=produit,
                defaults={'quantite': quantite}
            )
            
            if not created:
                ligne.quantite += quantite
                ligne.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{produit.nom} ajouté au panier',
                'panier_count': panier.nombre_items(),
                'panier_total': float(panier.total())
            })
            
        except Produit.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Produit introuvable'
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    }, status=405)





from django.core.mail import send_mail
from django.contrib import messages

def a_propos(request):
    """Page À propos de SahelVert"""
    return render(request, 'shop/a_propos.html')


def contact(request):
    """Page de contact avec formulaire"""
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        sujet = request.POST.get('sujet')
        message = request.POST.get('message')
        
        # Envoyer l'email
        try:
            send_mail(
                f'Contact SahelVert: {sujet}',
                f'De: {nom} ({email})\n\n{message}',
                email,
                ['contact@sahelvert.bf'],
                fail_silently=False,
            )
            messages.success(request, 'Message envoyé avec succès!')
        except:
            messages.error(request, 'Erreur lors de l\'envoi du message')
    
    return render(request, 'shop/contact.html')


def methodes_culture(request):
    """Page expliquant les méthodes de culture hors-sol"""
    return render(request, 'shop/methodes_culture.html')


def produits_par_categorie(request, categorie_id):
    """Affiche les produits d'une catégorie spécifique"""
    categorie = get_object_or_404(Categorie, id=categorie_id, actif=True)
    produits = Produit.objects.filter(
        categorie=categorie, 
        actif=True
    ).order_by('-date_creation')
    
    context = {
        'categorie': categorie,
        'produits': produits,
    }
    return render(request, 'shop/categorie.html', context)


def api_panier_count(request):
    """API pour obtenir le nombre d'articles dans le panier (AJAX)"""
    if request.user.is_authenticated:
        try:
            client = Client.objects.get(user=request.user)
            panier = Panier.objects.get(client=client)
            count = panier.nombre_items()
        except (Client.DoesNotExist, Panier.DoesNotExist):
            count = 0
    else:
        count = 0
    
    return JsonResponse({'count': count})


def paiement_callback(request):
    """
    Callback pour les paiements Mobile Money
    Cette vue reçoit les notifications des opérateurs
    """
    if request.method == 'POST':
        import json
        
        # Récupérer les données du callback
        data = json.loads(request.body)
        
        # Extraire les informations
        code_transaction = data.get('order_id')
        statut = data.get('status')
        reference = data.get('txnid')
        
        try:
            # Récupérer le paiement
            paiement = Paiement.objects.get(code_transaction=code_transaction)
            
            # Créer une transaction Mobile Money
            TransactionMobileMoney.objects.create(
                paiement=paiement,
                operateur=paiement.mode_paiement,
                numero_emetteur=paiement.numero_telephone,
                numero_recepteur='SAHELVERT',
                montant=paiement.montant,
                id_transaction_operateur=reference,
                statut_operateur=statut,
                reponse_json=data
            )
            
            # Mettre à jour le statut
            if statut == 'SUCCESS':
                paiement.confirmer_paiement(reference_externe=reference)
            elif statut == 'FAILED':
                paiement.marquer_comme_echoue('Paiement refusé par l\'opérateur')
            
            return JsonResponse({'status': 'ok'})
            
        except Paiement.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Paiement introuvable'}, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)


# ========== DOCUMENTATION COMPLÈTE ==========

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    SAHELVERT E-COMMERCE - DOCUMENTATION                     ║
║                        Système de vente en ligne                            ║
║                     Produits agricoles hors-sol                             ║
╚════════════════════════════════════════════════════════════════════════════╝

TABLE DES MATIÈRES
==================
1. Architecture du système
2. Modèles de données
3. Système de paiement
4. URLs et routes
5. Guide d'utilisation
6. Intégration API Mobile Money
7. Déploiement en production

─────────────────────────────────────────────────────────────────────────────

1. ARCHITECTURE DU SYSTÈME
===========================

Structure du projet:
sahelvert/
├── manage.py
├── requirements.txt
├── sahelvert/
│   ├── __init__.py
│   ├── settings.py         # Configuration Django
│   ├── urls.py             # Routes principales
│   └── wsgi.py
├── shop/                   # Application e-commerce
│   ├── models.py           # Modèles de données
│   ├── views.py            # Logique métier
│   ├── admin.py            # Interface admin
│   ├── urls.py             # Routes de l'app
│   └── migrations/         # Migrations BDD
├── templates/
│   └── shop/
│       ├── base.html
│       ├── accueil.html
│       ├── liste_produits.html
│       ├── detail_produit.html
│       ├── panier.html
│       ├── checkout.html
│       ├── confirmation.html
│       └── mes_commandes.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── media/
    ├── produits/
    └── categories/

─────────────────────────────────────────────────────────────────────────────

2. MODÈLES DE DONNÉES
======================

2.1 Categorie
-------------
- Organise les produits par type
- Champs: nom, description, image, actif

2.2 Produit
-----------
- Informations complètes sur chaque produit
- Champs: nom, catégorie, prix, stock, images (3 max)
- Gère les promotions et réductions
- Informations hors-sol: méthode culture, certifications
- Méthodes: prix_avec_promotion(), est_en_stock()

2.3 Client
----------
- Extension du modèle User Django
- Coordonnées: téléphone, adresse complète
- Relation OneToOne avec User

2.4 Panier
----------
- Panier temporaire par client
- Méthodes: total(), nombre_items()

2.5 LignePanier
---------------
- Items dans le panier
- Lié à un Panier et un Produit
- Gère les quantités

2.6 Commande
------------
- Statuts: en_attente, confirmee, en_preparation, en_livraison, livree, annulee
- Modes paiement: cash, orange_money, moov_money, carte
- Auto-génération numéro commande: SV{timestamp}
- Méthode: calculer_total()

2.7 LigneCommande
-----------------
- Produits dans une commande
- Sauvegarde prix/nom au moment de l'achat (historique)

2.8 Paiement
------------
- Gestion des transactions
- Statuts: en_attente, initie, reussi, echoue
- Code transaction unique: SV-PAY-{timestamp}-{random}
- Méthodes: initier_paiement(), confirmer_paiement()

2.9 TransactionMobileMoney
---------------------------
- Détails techniques des transactions
- Logs des requêtes/réponses API
- Pour réconciliation comptable

─────────────────────────────────────────────────────────────────────────────

3. SYSTÈME DE PAIEMENT
=======================

3.1 Paiement à la livraison (Cash)
-----------------------------------
- Aucune transaction préalable
- Paiement en espèces lors de la réception
- Statut: en_attente jusqu'à livraison

3.2 Orange Money
----------------
Process:
1. Client choisit Orange Money au checkout
2. Système crée un Paiement avec code unique
3. SMS envoyé au client avec instructions
4. Client valide via #144#
5. Callback de l'API Orange confirme le paiement
6. Commande automatiquement confirmée

Intégration API (à compléter):
- Endpoint: https://api.orange.com/orange-money-webpay/
- Authentification: OAuth2
- Méthode: initiate_payment()

3.3 Moov Money
--------------
Process similaire à Orange Money
- Validation via #555#
- API Moov Money (à intégrer)

Code d'intégration (exemple):

    def initier_paiement_orange(paiement):
        import requests
        
        url = "https://api.orange.com/orange-money-webpay/v1/webpayment"
        headers = {
            "Authorization": f"Bearer {ORANGE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "merchant_key": ORANGE_MERCHANT_KEY,
            "currency": "XOF",
            "order_id": paiement.code_transaction,
            "amount": int(paiement.montant),
            "return_url": f"{SITE_URL}/paiement/retour/",
            "cancel_url": f"{SITE_URL}/paiement/annulation/",
            "notif_url": f"{SITE_URL}/api/paiement/callback/",
            "lang": "fr",
            "reference": paiement.commande.numero_commande
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            paiement.reference_externe = result['payment_token']
            paiement.statut = 'initie'
            paiement.save()
            return True
        
        return False

─────────────────────────────────────────────────────────────────────────────

4. URLS ET ROUTES
=================

Pages publiques:
----------------
/                           # Accueil
/produits/                  # Liste des produits
/produit/<id>/              # Détail produit

Panier et commandes (auth requise):
------------------------------------
/panier/                    # Voir le panier
/ajouter-au-panier/<id>/    # Ajouter au panier
/modifier-panier/<id>/      # Modifier quantité
/supprimer-du-panier/<id>/  # Retirer du panier
/vider-panier/              # Vider le panier
/commander/                 # Checkout
/confirmation/<id>/         # Confirmation commande
/mes-commandes/             # Liste mes commandes
/commande/<id>/             # Détail d'une commande
/annuler-commande/<id>/     # Annuler commande

API (optionnel):
----------------
/api/ajouter-panier/        # AJAX ajouter au panier
/api/paiement/callback/     # Callback Mobile Money

Administration:
---------------
/admin/                     # Interface Django Admin

─────────────────────────────────────────────────────────────────────────────

5. GUIDE D'UTILISATION
=======================

5.1 Pour l'administrateur
--------------------------
1. Accéder à /admin/
2. Créer des catégories de produits
3. Ajouter des produits avec photos
4. Gérer les stocks
5. Suivre les commandes
6. Confirmer les paiements manuellement si nécessaire

5.2 Pour le client
-------------------
1. Parcourir les produits
2. Ajouter au panier
3. Finaliser la commande
4. Choisir mode de paiement
5. Valider le paiement (si Mobile Money)
6. Suivre sa commande

─────────────────────────────────────────────────────────────────────────────

6. DÉPLOIEMENT EN PRODUCTION
=============================

6.1 Prérequis
-------------
- Serveur Linux (Ubuntu recommandé)
- Python 3.8+
- PostgreSQL ou MySQL
- Nginx
- Gunicorn
- Certificat SSL (Let's Encrypt)

6.2 Installation
----------------
# 1. Cloner le projet
git clone https://github.com/votre-repo/sahelvert.git
cd sahelvert

# 2. Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env
nano .env  # Configurer les variables

# 5. Base de données
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

# 6. Gunicorn
gunicorn sahelvert.wsgi:application --bind 0.0.0.0:8000

# 7. Nginx (fichier de config)
server {
    listen 80;
    server_name sahelvert.bf www.sahelvert.bf;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    
    location /static/ {
        alias /var/www/sahelvert/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/sahelvert/media/;
    }
}

6.3 Sécurité
------------
- DEBUG = False
- SECRET_KEY unique et complexe
- ALLOWED_HOSTS configuré
- HTTPS activé
- Firewall configuré
- Backups réguliers BDD

─────────────────────────────────────────────────────────────────────────────

7. SUPPORT ET CONTACT
======================
Email: contact@sahelvert.bf
Téléphone: +226 XX XX XX XX
WhatsApp: +226 XX XX XX XX

╔════════════════════════════════════════════════════════════════════════════╗
║                    © 2025 SahelVert - Tous droits réservés                 ║
╚════════════════════════════════════════════════════════════════════════════╝
"""