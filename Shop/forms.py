from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Client

class RegisterForm(UserCreationForm):
    # Champs communs avec classes responsives
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Nom d\'utilisateur'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Mot de passe'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Confirmer le mot de passe'
    }))
    
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Email'
    }))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Prénom'
    }))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Nom'
    }))
    telephone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Téléphone'
    }))
    adresse = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Adresse',
        'rows': 3
    }), required=False)
    ville = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Ville'
    }))
    quartier = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Quartier'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                  'telephone', 'adresse', 'ville', 'quartier']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            Client.objects.create(
                user=user,
                telephone=self.cleaned_data['telephone'],
                ville=self.cleaned_data['ville'],
                quartier=self.cleaned_data['quartier']
            )
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Nom d\'utilisateur ou email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg', 
        'placeholder': 'Mot de passe'
    }))