from django import forms

_FILE = {"required": "Déposez le fichier reçu et son certificat."}


class PublicVerifyForm(forms.Form):
    file = forms.FileField(allow_empty_file=True, error_messages=_FILE)
    certificate = forms.FileField(allow_empty_file=True, error_messages=_FILE)

    def clean_file(self):
        from django.conf import settings
        from vault.forms import too_large_message
        f = self.cleaned_data["file"]
        if f.size > settings.SCEAU_MAX_UPLOAD_BYTES:
            raise forms.ValidationError(too_large_message())
        return f
