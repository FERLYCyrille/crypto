from django.urls import path

from . import views

urlpatterns = [
    path("coffre", views.vault_list, name="vault_list"),
    path("coffre/<uuid:pk>/verifier", views.vault_verify, name="vault_verify"),
]
