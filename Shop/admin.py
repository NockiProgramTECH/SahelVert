# ========== admin.py - Interface d'administration Django ==========

from django.contrib import admin
from .models import (
    Categorie, Produit, Client, Commande, 
    LigneCommande, Panier, LignePanier, Avis
)

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    """
    Administration des catégories de produits
    """
    list_display = ['nom', 'actif', 'date_creation']
    list_filter = ['actif', 'date_creation']
    search_fields = ['nom', 'description']
    list_editable = ['actif']


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    """
    Administration des produits hors-sol
    """
    list_display = [
        'nom', 'categorie', 'prix', 'unite', 
        'stock', 'en_promotion', 'actif',
        'par_commande'
    ]
    list_filter = ['categorie', 'actif', 'en_promotion', 'unite']
    search_fields = ['nom', 'description']
    list_editable = ['prix', 'stock', 'actif', 'en_promotion','par_commande']
    readonly_fields = ['date_creation', 'date_modification']
    list_per_page=7
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'categorie', 'description', 'prix', 'unite', 'stock')
        }),
        ('Images', {
            'fields': ('image', 'image_2', 'image_3')
        }),

        ('Culture hors-sol', {
            'fields': ('methode_culture', 'certifications')
        }),
        ('Promotions', {
            'fields': ('en_promotion', 'pourcentage_promotion')
        }),
        ('Gestion', {
            'fields': ('actif', 'date_creation', 'date_modification')
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Administration des clients
    """
    list_display = ['user', 'telephone', 'ville', 'quartier', 'date_inscription']
    list_filter = ['ville', 'date_inscription']
    search_fields = ['user__username', 'user__email', 'telephone', 'ville']
    readonly_fields = ['date_inscription']


class LigneCommandeInline(admin.TabularInline):
    """
    Affichage en ligne des produits dans une commande
    """
    model = LigneCommande
    extra = 0
    readonly_fields = ['sous_total']
    
    def sous_total(self, obj):
        return f"{obj.sous_total()} FCFA"


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    """
    Administration des commandes
    """
    list_display = [
        'numero_commande', 'client', 'statut', 
        'total', 'mode_paiement', 'paiement_effectue', 'date_commande'
    ]
    list_filter = ['statut', 'mode_paiement', 'paiement_effectue', 'date_commande']
    search_fields = ['numero_commande', 'client__user__username']
    readonly_fields = ['numero_commande', 'date_commande', 'date_modification']
    list_editable = ['statut', 'paiement_effectue']
    inlines = [LigneCommandeInline]
    
    fieldsets = (
        ('Client', {
            'fields': ('client', 'numero_commande')
        }),
        ('Statut', {
            'fields': ('statut', 'mode_paiement', 'paiement_effectue')
        }),
        ('Livraison', {
            'fields': (
                'adresse_livraison', 'ville_livraison', 
                'quartier_livraison', 'telephone_livraison'
            )
        }),
        ('Montants', {
            'fields': ('sous_total', 'frais_livraison', 'total')
        }),
        ('Notes', {
            'fields': ('notes_client', 'notes_interne')
        }),
        ('Dates', {
            'fields': (
                'date_commande', 'date_livraison_prevue', 
                'date_livraison_reelle', 'date_modification'
            )
        }),
    )
    
    actions = ['marquer_comme_confirmee', 'marquer_comme_livree']
    
    def marquer_comme_confirmee(self, request, queryset):
        """Action pour confirmer plusieurs commandes"""
        updated = queryset.update(statut='confirmee')
        self.message_user(request, f'{updated} commande(s) confirmée(s).')
    marquer_comme_confirmee.short_description = "Marquer comme confirmée"
    
    def marquer_comme_livree(self, request, queryset):
        """Action pour marquer plusieurs commandes comme livrées"""
        from django.utils import timezone
        updated = queryset.update(
            statut='livree',
            date_livraison_reelle=timezone.now()
        )
        self.message_user(request, f'{updated} commande(s) marquée(s) comme livrée(s).')
    marquer_comme_livree.short_description = "Marquer comme livrée"


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    """
    Administration des avis clients
    """
    list_display = ['produit', 'client', 'note', 'approuve', 'date_creation']
    list_filter = ['note', 'approuve', 'date_creation']
    search_fields = ['produit__nom', 'client__user__username', 'commentaire']
    list_editable = ['approuve']
    readonly_fields = ['date_creation']





# ========== admin.py (Extension) - Administration des Paiements ==========

from django.contrib import admin
from .models import Paiement, TransactionMobileMoney

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    """
    Administration des paiements
    """
    list_display = [
        'code_transaction', 'commande', 'montant', 
        'mode_paiement', 'statut', 'date_creation'
    ]
    list_filter = ['statut', 'mode_paiement', 'date_creation']
    search_fields = [
        'code_transaction', 'reference_externe', 
        'numero_telephone', 'commande__numero_commande'
    ]
    readonly_fields = [
        'code_transaction', 'date_creation', 
        'date_initiation', 'date_completion'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': (
                'commande', 'montant', 'mode_paiement', 
                'statut', 'code_transaction'
            )
        }),
        ('Mobile Money', {
            'fields': ('numero_telephone', 'reference_externe')
        }),
        ('Dates', {
            'fields': (
                'date_creation', 'date_initiation', 'date_completion'
            )
        }),
        ('Détails', {
            'fields': ('message_erreur', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirmer_paiements', 'marquer_comme_echoue']
    
    def confirmer_paiements(self, request, queryset):
        """Action pour confirmer plusieurs paiements"""
        for paiement in queryset:
            paiement.confirmer_paiement()
        self.message_user(
            request, 
            f'{queryset.count()} paiement(s) confirmé(s).'
        )
    confirmer_paiements.short_description = "Confirmer les paiements"
    
    def marquer_comme_echoue(self, request, queryset):
        """Action pour marquer plusieurs paiements comme échoués"""
        updated = queryset.update(statut='echoue')
        self.message_user(
            request, 
            f'{updated} paiement(s) marqué(s) comme échoué(s).'
        )
    marquer_comme_echoue.short_description = "Marquer comme échoué"


@admin.register(TransactionMobileMoney)
class TransactionMobileMoneyAdmin(admin.ModelAdmin):
    """
    Administration des transactions Mobile Money
    """
    list_display = [
        'id_transaction_operateur', 'operateur', 
        'montant', 'statut_operateur', 'date_tentative'
    ]
    list_filter = ['operateur', 'statut_operateur', 'date_tentative']
    search_fields = [
        'id_transaction_operateur', 'numero_emetteur', 
        'paiement__code_transaction'
    ]
    readonly_fields = [
        'date_tentative', 'date_callback', 
        'requete_json', 'reponse_json'
    ]

