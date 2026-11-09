from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def invite_to_read_the_guide(sender, request, user, **kwargs):
    """À chaque connexion (et après l'inscription), on invite à lire le guide.
    Le texte est rendu par base.html grâce au tag « guide »."""
    messages.info(request, "guide", extra_tags="guide", fail_silently=True)
