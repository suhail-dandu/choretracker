from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Family


class FamilyRegistrationForm(forms.Form):
    """Step 1: Parent creates the family."""
    family_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'e.g. The Smith Family'})
    )
    currency_symbol = forms.ChoiceField(
        choices=[('€', '€ Euro'), ('£', '£ Pound'), ('$', '$ Dollar'), ('kr', 'kr Krone')],
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Your first name'})
    )
    last_name = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Your last name'})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Choose a username'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Create a password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Repeat password'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords don't match.")
        return cleaned_data


class JoinFamilyForm(forms.Form):
    """Join existing family with invite code."""
    invite_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Enter invite code'})
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Your first name'})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Choose a username'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'})
    )
    avatar = forms.ChoiceField(
        choices=User.AVATAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )

    def clean_invite_code(self):
        code = self.cleaned_data['invite_code'].upper()
        try:
            return Family.objects.get(invite_code=code)
        except Family.DoesNotExist:
            raise forms.ValidationError("Invalid invite code. Ask your parent!")

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords don't match.")
        return cleaned_data


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Password'})
    )


class AddChildForm(forms.ModelForm):
    """Parent adds a child directly."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Temporary password for the child."
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'avatar', 'date_of_birth']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.Select(attrs={'class': 'form-select', 'id': 'avatarSelect'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class AdjustPointsForm(forms.Form):
    """Admin manually adjusts points for a child."""
    points = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'e.g. 50 or -20'}),
        help_text="Positive to add, negative to deduct."
    )
    reason = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason for adjustment'}),
        required=False
    )
