from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    username = UsernameField(label="E-mail", widget=forms.TextInput(
        attrs={"autofocus": True, "autocomplete": "email", "class": "in"}))
    password = forms.CharField(label="Mot de passe", strip=False, widget=forms.PasswordInput(
        attrs={"autocomplete": "current-password", "class": "in"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class SignupForm(forms.Form):
    email = forms.EmailField(label="E-mail", widget=forms.EmailInput(
        attrs={"autocomplete": "email", "class": "in"}))
    name = forms.CharField(label="Nom affiché (il figurera sur vos certificats)", max_length=60,
                           widget=forms.TextInput(attrs={"autocomplete": "name", "class": "in"}))
    password1 = forms.CharField(label="Mot de passe", strip=False, widget=forms.PasswordInput(
        attrs={"autocomplete": "new-password", "class": "in"}))
    password2 = forms.CharField(label="Confirmer le mot de passe", strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password",
                                                                  "class": "in"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise ValidationError("Cette adresse e-mail ne peut pas être utilisée.")
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les deux mots de passe ne correspondent pas.")
        elif p1:
            candidate = User(username=data.get("email", ""), first_name=data.get("name", ""))
            try:
                validate_password(p1, user=candidate)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return data

    def save(self):
        d = self.cleaned_data
        return User.objects.create_user(username=d["email"], email=d["email"],
                                        password=d["password1"], first_name=d["name"].strip())
