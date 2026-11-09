from django import forms
from django.conf import settings


def too_large_message() -> str:
    limit = settings.SCEAU_MAX_UPLOAD_BYTES
    size = f"{limit // (1024 * 1024)} Mo" if limit >= 1024 * 1024 else f"{limit} octets"
    return f"Ce fichier dépasse {size}. Choisissez un fichier plus léger."


class UploadForm(forms.Form):
    file = forms.FileField(allow_empty_file=True,
                           error_messages={"required": "Choisissez un fichier."})

    def clean_file(self):
        f = self.cleaned_data["file"]
        if f.size > settings.SCEAU_MAX_UPLOAD_BYTES:
            raise forms.ValidationError(too_large_message())
        return f
