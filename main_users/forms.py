# main_users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import MainUser

class UserRegistrationForm(UserCreationForm):
    """Form for user registration, extending UserCreationForm."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email',
    }))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your first name',
    }))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your last name',
    }))
    country = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your country',
    }))
    language = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your language',
    }))
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = MainUser
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name', 'country', 'language', 'profile_picture']


from django import forms
from .models import MainUser

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""

    class Meta:
        model = MainUser
        fields = ['email', 'first_name', 'last_name', 'profile_picture', 'country', 'language']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.TextInput(attrs={'class': 'form-control'}),
        }
