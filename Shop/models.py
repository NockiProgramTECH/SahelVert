"""
=============================================================================
SAHELVERT E-COMMERCE - SYSTÈME DE VENTE DE PRODUITS HORS-SOL
=============================================================================

Description:
    Site e-commerce pour la vente de produits agricoles hors-sol
    (légumes, fruits, laitues, etc.) cultivés en hydroponie/aquaponie.

Structure:
    - models.py: Modèles de données
    - views.py: Vues et logique métier
    - urls.py: Configuration des URLs
    - admin.py: Interface d'administration
    - settings.py: Configuration Django

Technologies:
    - Django 4.x
    - PostgreSQL/MySQL (base de données)
    - Bootstrap 5 (frontend)
    - Pillow (gestion d'images)

Installation:
    1. pip install django pillow
    2. python manage.py makemigrations
    3. python manage.py migrate
    4. python manage.py createsuperuser
    5. python manage.py runserver

=============================================================================
"""

# ========== models.py - Modèles de données pour SahelVert E-commerce ==========

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Categorie(models.Model):
    """
    Modèle pour les catégories de produits (légumes, fruits, laitues, etc.)
    """
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Produit(models.Model):
    """
    Modèle pour les produits hors-sol (légumes, fruits, laitues)
    """
    UNITE_CHOICES = [
        ('kg', 'Kilogramme'),
        ('piece', 'Pièce'),
        ('botte', 'Botte'),
        ('sachet', 'Sachet'),
    ]
    
    nom = models.CharField(max_length=200)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='produits')
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unite = models.CharField(max_length=10, choices=UNITE_CHOICES, default='kg')
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    par_commande =models.BooleanField(default =False ,help_text="Indique si le produit doit se daire par commande")

    image = models.ImageField(upload_to='produits/')
    image_2 = models.ImageField(upload_to='produits/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='produits/', blank=True, null=True)

    
    # # Informations nutritionnelles (optionnel)
    # calories = models.IntegerField(blank=True, null=True, help_text="Calories pour 100g")
    # vitamines = models.CharField(max_length=200, blank=True)
    
    # Informations de culture hors-sol
    mth_choice=[
        ("Hydroponie","Hydronponie"),
        ("Aquaponie","Aquaponie"),
    ]
    methode_culture = models.CharField(max_length=100, blank=True,choices=mth_choice)
    cer_choice =[
        ("Bio","Bio"),
        ("Sans pesticides","Sans pesticides"),
    ]
    certifications = models.CharField(max_length=200, blank=True, choices =cer_choice)

    
    # Gestion
    actif = models.BooleanField(default=True)
    en_promotion = models.BooleanField(default=False)
    pourcentage_promotion = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.nom} - {self.prix} FCFA/{self.unite}"
    
    def prix_avec_promotion(self):
        """Calcule le prix après promotion si applicable"""
        if self.en_promotion and self.pourcentage_promotion > 0:
            reduction = self.prix * (self.pourcentage_promotion / 100)
            return self.prix - reduction
        return self.prix
    
    def est_en_stock(self):
        """Vérifie si le produit est disponible en stock"""
        return self.stock > 0


class Client(models.Model):
    """
    Modèle pour les clients du site
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10, blank=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.telephone}"


class Commande(models.Model):
    """
    Modèle pour les commandes des clients
    """
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_preparation', 'En préparation'),
        ('en_livraison', 'En livraison'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    
    MODE_PAIEMENT_CHOICES = [
        ('cash', 'Paiement à la livraison'),
        ('orange_money', 'Orange Money'),
        ('moov_money', 'Moov Money'),
        ('carte', 'Carte bancaire'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commandes')
    numero_commande = models.CharField(max_length=20, unique=True, editable=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    
    # Adresse de livraison
    adresse_livraison = models.TextField()
    ville_livraison = models.CharField(max_length=100)
    quartier_livraison = models.CharField(max_length=100)
    telephone_livraison = models.CharField(max_length=20)
    
    # Montants
    sous_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frais_livraison = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Paiement
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES)
    paiement_effectue = models.BooleanField(default=False)
    
    # Notes et suivi
    notes_client = models.TextField(blank=True, help_text="Instructions spéciales du client")
    notes_interne = models.TextField(blank=True, help_text="Notes pour l'équipe")
    
    # Dates
    date_commande = models.DateTimeField(auto_now_add=True)
    date_livraison_prevue = models.DateTimeField(blank=True, null=True)
    date_livraison_reelle = models.DateTimeField(blank=True, null=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_commande']
    
    def __str__(self):
        return f"Commande {self.numero_commande} - {self.client.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Génère un numéro de commande unique si non existant"""
        if not self.numero_commande:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.numero_commande = f"SV{timestamp}"
        super().save(*args, **kwargs)
    

    def calculer_frais_livraison(self):
        """Calcule les frais de livraison en fonction de la ville"""
        frais_base = Decimal('1000')  # Frais de base en FCFA
        if self.ville_livraison.lower() == 'ouagadougou':
            self.frais_livraison = frais_base
        else:
            self.frais_livraison = frais_base + Decimal('300')  # Supplément pour autres villes
        self.save()


    def calculer_total(self):
        """Calcule le total de la commande"""
        self.sous_total = sum(item.sous_total() for item in self.items.all())
        self.total = self.sous_total + self.frais_livraison
        self.save()


class LigneCommande(models.Model):
    """
    Modèle pour les lignes de commande (produits dans une commande)
    """
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='items')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    
    # Informations au moment de la commande (pour historique)
    nom_produit = models.CharField(max_length=200)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    quantite = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unite = models.CharField(max_length=10)
    
    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"
    
    def __str__(self):
        return f"{self.nom_produit} x {self.quantite} {self.unite}"
    
    def sous_total(self):
        """Calcule le sous-total de cette ligne"""
        return self.prix_unitaire * self.quantite
    
    def save(self, *args, **kwargs):
        """Sauvegarde les infos du produit au moment de la commande"""
        if not self.nom_produit:
            self.nom_produit = self.produit.nom
        if not self.prix_unitaire:
            self.prix_unitaire = self.produit.prix_avec_promotion()
        if not self.unite:
            self.unite = self.produit.unite
        super().save(*args, **kwargs)


class Panier(models.Model):
    """
    Modèle pour le panier d'achat temporaire
    """
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='panier')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
    
    def __str__(self):
        return f"Panier de {self.client.user.get_full_name()}"
    
    def total(self):
        """Calcule le total du panier"""
        return sum(item.sous_total() for item in self.items.all())
    
    def nombre_items(self):
        """Retourne le nombre total d'articles dans le panier"""
        return sum(item.quantite for item in self.items.all())


class LignePanier(models.Model):
    """
    Modèle pour les lignes du panier
    """
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='items')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.IntegerField(default=1, validators=[MinValueValidator(1)])


    
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ligne de panier"
        verbose_name_plural = "Lignes de panier"
        unique_together = ['panier', 'produit']
    
    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"
    
    def sous_total(self):
        """Calcule le sous-total de cette ligne"""
        return self.produit.prix_avec_promotion() * self.quantite


class Avis(models.Model):
    """
    Modèle pour les avis clients sur les produits
    """
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='avis')
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    note = models.IntegerField(
        validators=[MinValueValidator(1), MinValueValidator(5)],
        help_text="Note de 1 à 5 étoiles"
    )
    commentaire = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    approuve = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-date_creation']
        unique_together = ['produit', 'client']
    
    def __str__(self):
        return f"Avis de {self.client.user.get_full_name()} sur {self.produit.nom}"
    



# ========== models.py (Extension) - Modèle de Paiement ==========

"""
Extension des modèles pour gérer les paiements Mobile Money
(Orange Money, Moov Money) et les paiements en espèces
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
import secrets

# Ajoutez ce modèle aux modèles existants

class Paiement(models.Model):
    """
    Modèle pour suivre les paiements des commandes
    Supporte Orange Money, Moov Money et paiement cash
    """
    MODE_PAIEMENT_CHOICES = [
        ('cash', 'Paiement à la livraison'),
        ('orange_money', 'Orange Money'),
        ('moov_money', 'Moov Money'),
        ('carte', 'Carte bancaire'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('initie', 'Initié'),
        ('en_cours', 'En cours'),
        ('reussi', 'Réussi'),
        ('echoue', 'Échoué'),
        ('annule', 'Annulé'),
        ('rembourse', 'Remboursé'),
    ]
    
    # Informations de base
    commande = models.OneToOneField(
        'Commande', 
        on_delete=models.CASCADE, 
        related_name='paiement'
    )
    montant = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    mode_paiement = models.CharField(
        max_length=20, 
        choices=MODE_PAIEMENT_CHOICES
    )
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='en_attente'
    )
    
    # Informations Mobile Money
    numero_telephone = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Numéro de téléphone pour Mobile Money"
    )
    code_transaction = models.CharField(
        max_length=50, 
        unique=True, 
        editable=False,
        help_text="Code unique de transaction"
    )
    reference_externe = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Référence du fournisseur de paiement"
    )
    
    # Détails de la transaction
    date_creation = models.DateTimeField(auto_now_add=True)
    date_initiation = models.DateTimeField(blank=True, null=True)
    date_completion = models.DateTimeField(blank=True, null=True)
    
    # Informations supplémentaires
    message_erreur = models.TextField(
        blank=True,
        help_text="Message d'erreur si le paiement échoue"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données supplémentaires de la transaction"
    )
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Paiement {self.code_transaction} - {self.montant} FCFA"
    
    def save(self, *args, **kwargs):
        """Génère un code de transaction unique"""
        if not self.code_transaction:
            # Format: SV-PAYMENT-YYYYMMDDHHMMSS-RANDOM
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_code = secrets.token_hex(4).upper()
            self.code_transaction = f"SV-PAY-{timestamp}-{random_code}"
        super().save(*args, **kwargs)
    
    def initier_paiement(self):
        """
        Initie le processus de paiement Mobile Money
        Cette méthode devrait être étendue pour intégrer les APIs
        des opérateurs (Orange Money, Moov Money)
        """
        if self.mode_paiement in ['orange_money', 'moov_money']:
            self.statut = 'initie'
            self.date_initiation = timezone.now()
            
            # TODO: Intégrer l'API de l'opérateur
            # Exemple pour Orange Money:
            # response = orange_money_api.initiate_payment(
            #     amount=self.montant,
            #     phone_number=self.numero_telephone,
            #     reference=self.code_transaction
            # )
            
            self.save()
            return True
        return False
    
    def confirmer_paiement(self, reference_externe=None):
        """Confirme que le paiement a été effectué avec succès"""
        self.statut = 'reussi'
        self.date_completion = timezone.now()
        if reference_externe:
            self.reference_externe = reference_externe
        self.save()
        
        # Mettre à jour la commande
        self.commande.paiement_effectue = True
        self.commande.statut = 'confirmee'
        self.commande.save()
        
        return True
    
    def marquer_comme_echoue(self, message_erreur):
        """Marque le paiement comme échoué"""
        self.statut = 'echoue'
        self.message_erreur = message_erreur
        self.save()
        return True


class TransactionMobileMoney(models.Model):
    """
    Modèle pour suivre les transactions Mobile Money en détail
    Utile pour la réconciliation et le suivi
    """
    paiement = models.ForeignKey(
        Paiement, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    operateur = models.CharField(
        max_length=20,
        choices=[
            ('orange_money', 'Orange Money'),
            ('moov_money', 'Moov Money'),
        ]
    )
    numero_emetteur = models.CharField(max_length=20)
    numero_recepteur = models.CharField(max_length=20)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    frais = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Détails de l'opérateur
    id_transaction_operateur = models.CharField(max_length=100, unique=True)
    statut_operateur = models.CharField(max_length=50)
    message_operateur = models.TextField(blank=True)
    
    # Horodatage
    date_tentative = models.DateTimeField(auto_now_add=True)
    date_callback = models.DateTimeField(blank=True, null=True)
    
    # Données brutes
    requete_json = models.JSONField(
        default=dict,
        help_text="Requête envoyée à l'opérateur"
    )
    reponse_json = models.JSONField(
        default=dict,
        help_text="Réponse reçue de l'opérateur"
    )
    
    class Meta:
        verbose_name = "Transaction Mobile Money"
        verbose_name_plural = "Transactions Mobile Money"
        ordering = ['-date_tentative']
    
    def __str__(self):
        return f"{self.operateur} - {self.montant} FCFA"

