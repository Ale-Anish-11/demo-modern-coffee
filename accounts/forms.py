from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re


class CustomerRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 placeholder-stone-400 bg-stone-50',
            'placeholder': 'e.g. John Doe',
            'autocomplete': 'name',
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 placeholder-stone-400 bg-stone-50',
            'placeholder': 'e.g. johndoe',
            'autocomplete': 'username',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 placeholder-stone-400 bg-stone-50',
            'placeholder': 'john@example.com',
            'autocomplete': 'email',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 placeholder-stone-400 bg-stone-50',
            'placeholder': '98XXXXXXXX or +977-98...',
            'autocomplete': 'tel',
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 placeholder-stone-400 bg-stone-50',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 placeholder-stone-400 bg-stone-50',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        # Basic mobile phone validation (digits, plus sign, spaces, hyphens)
        clean_digits = re.sub(r'[\s\-+]', '', phone)
        if len(clean_digits) < 7:
            raise ValidationError("Please provide a valid phone number.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error('password', e)
        return cleaned_data


class CustomerLoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 placeholder-stone-400 bg-stone-50',
            'placeholder': 'Enter your username or email',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 placeholder-stone-400 bg-stone-50',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-amber-700 focus:ring-amber-500 h-4 w-4 border-stone-300'
        })
    )


class CustomerProfileUpdateForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 bg-white',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 bg-white',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 bg-white',
            'placeholder': '98XXXXXXXX',
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none transition text-stone-800 bg-white resize-none',
            'rows': 3,
            'placeholder': 'Street address, City, Area',
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.user and User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("This email is already in use by another account.")
        return email
