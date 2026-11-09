from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import AuditEvent


@login_required
def history(request):
    events = AuditEvent.objects.filter(user=request.user)[:200]
    return render(request, "audit/history.html", {"events": events, "section": "historique"})
