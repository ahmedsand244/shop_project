from django import forms
from django.contrib.auth.models import User
from .models import Review, ContactMessage


class ExtendedRegisterForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'John Doe',
            'autocomplete': 'name'
        })
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'johndoe',
            'autocomplete': 'username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'john@example.com',
            'autocomplete': 'email'
        })
    )
    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+20 100 000 0000',
            'autocomplete': 'tel'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Cairo / Alexandria'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 2,
            'placeholder': 'Primary shipping address (street, building, apartment)'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already registered.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cod', 'Cash On Delivery'),
        ('card', 'Credit / Debit Card'),
        ('wallet', 'Vodafone Cash / Mobile Wallet'),
    ]

    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Full Name'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'name@example.com'
        })
    )
    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+20 100 000 0000'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'City (e.g. Cairo, Alexandria)'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 3,
            'placeholder': 'Street, Building number, Apartment, Landmark'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 2,
            'placeholder': 'Special delivery notes or instructions (optional)'
        })
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect,
        initial='cod'
    )
    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_latitude'})
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_longitude'})
    )


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+20 100 000 0000'}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Subject / Inquiry Topic'}),
            'message': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'How may our concierge assist you?'}),
        }


class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (5, '5/5 - Outstanding Excellence'),
        (4, '4/5 - Highly Recommended'),
        (3, '3/5 - Satisfactory'),
        (2, '2/5 - Below Expectations'),
        (1, '1/5 - Unsatisfactory'),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'}),
        initial=5
    )
    title = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Review Headline'
        })
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 4,
            'placeholder': 'Share your detailed experience with this product...'
        })
    )

    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
