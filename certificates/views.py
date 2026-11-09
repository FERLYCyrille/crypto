from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.ratelimit import rate_limit
from sceau_crypto import signing
from sceau_crypto.hashing import FileTooLarge
from vault.forms import too_large_message
from vault.models import FileRecord

from . import keys, services
from .forms import PublicVerifyForm
from .models import Certificate


@login_required
@require_POST
def certify(request, pk):
    record = get_object_or_404(FileRecord, pk=pk, owner=request.user)
    cert = services.issue_certificate(user=request.user, record=record)
    messages.success(request, "Certificat émis.")
    return redirect("certificate_detail", pk=cert.pk)


@login_required
def certificate_list(request):
    certs = Certificate.objects.filter(owner=request.user)
    return render(request, "certificates/list.html", {"certs": certs, "section": "certificats"})


@login_required
def certificate_detail(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, owner=request.user)
    return render(request, "certificates/detail.html", {
        "cert": cert, "payload": cert.document.get("payload", {}), "section": "certificats",
        "verify_url": request.build_absolute_uri(reverse("public_verify"))})


@login_required
def certificate_download(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, owner=request.user)
    response = HttpResponse(services.certificate_bytes(cert), content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="certificat-{cert.serial}.json"'
    return response


def _issued_datetime(payload):
    try:
        return datetime.strptime(payload["issued_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None


@rate_limit("public_verify", 20, 60)
def public_verify(request):
    ctx = {"section": "verifier"}
    if request.method == "POST":
        form = PublicVerifyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                result = services.verify_received(
                    certificate_stream=form.cleaned_data["certificate"],
                    file_stream=form.cleaned_data["file"])
            except FileTooLarge:
                ctx["error"] = too_large_message()
            else:
                ctx["result"] = result
                if result.payload:
                    ctx["issued_at"] = _issued_datetime(result.payload)
        else:
            ctx["error"] = next(iter(form.errors.values()))[0]
    return render(request, "certificates/verify_public.html", ctx)


def public_key(request):
    key_id = settings.SCEAU_KEY_ID
    public = keys.get_public_keys()[key_id]
    return render(request, "certificates/public_key.html", {
        "key_id": key_id, "fingerprint": signing.public_key_fingerprint(public),
        "pem": Path(settings.SCEAU_PUBLIC_KEY_PATH).read_text(encoding="utf-8"),
        "section": "verifier"})
