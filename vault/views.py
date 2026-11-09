from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render

from sceau_crypto.hashing import FileTooLarge

from . import services
from .forms import UploadForm, too_large_message
from .models import FileRecord, Verification


def _first_error(form):
    return next(iter(form.errors.values()))[0]


@login_required
def vault_list(request):
    error = None
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data["file"]
            try:
                record = services.register_file(user=request.user, stream=f, filename=f.name)
            except FileTooLarge:
                error = too_large_message()
            else:
                messages.success(request, f"« {record.filename} » est enregistré dans votre coffre.")
                return redirect("vault_list")
        else:
            error = _first_error(form)
    last = (Verification.objects.filter(record=OuterRef("pk"))
            .order_by("-performed_at").values("result")[:1])
    records = FileRecord.objects.filter(owner=request.user).annotate(last_result=Subquery(last))
    return render(request, "vault/coffre.html",
                  {"records": records, "error": error, "section": "coffre"})


@login_required
def vault_verify(request, pk):
    record = get_object_or_404(FileRecord, pk=pk, owner=request.user)
    ctx = {"record": record, "section": "coffre"}
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                ctx["verification"] = services.verify_file(
                    user=request.user, record=record, stream=form.cleaned_data["file"])
            except FileTooLarge:
                ctx["error"] = too_large_message()
        else:
            ctx["error"] = _first_error(form)
    return render(request, "vault/verify.html", ctx)
