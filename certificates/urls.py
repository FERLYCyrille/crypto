from django.urls import path

from . import views

urlpatterns = [
    path("coffre/<uuid:pk>/certifier", views.certify, name="certify"),
    path("certificats", views.certificate_list, name="certificate_list"),
    path("certificats/<int:pk>", views.certificate_detail, name="certificate_detail"),
    path("certificats/<int:pk>/telecharger", views.certificate_download,
         name="certificate_download"),
    path("verifier-certificat", views.public_verify, name="public_verify"),
    path("cle-publique", views.public_key, name="public_key"),
]
