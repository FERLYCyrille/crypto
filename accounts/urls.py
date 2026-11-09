from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import EmailAuthenticationForm
from .ratelimit import rate_limit

login_view = rate_limit("login", 10, 60)(LoginView.as_view(
    template_name="accounts/login.html", authentication_form=EmailAuthenticationForm,
    redirect_authenticated_user=True))

urlpatterns = [
    path("connexion", login_view, name="login"),
    path("inscription", views.signup, name="signup"),
    path("guide", views.guide, name="guide"),
    path("deconnexion", LogoutView.as_view(), name="logout"),
]
