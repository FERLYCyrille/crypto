from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignupForm
from .ratelimit import rate_limit


@rate_limit("signup", 10, 60)
def signup(request):
    if request.user.is_authenticated:
        return redirect("vault_list")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("vault_list")
    return render(request, "accounts/signup.html", {"form": form})


def guide(request):
    """Page d'information : accessible à tous, connectés ou non."""
    return render(request, "guide.html", {
        "section": "guide", "max_mb": settings.SCEAU_MAX_UPLOAD_BYTES // (1024 * 1024)})
