"""Limitation simple par adresse IP (cache Django). Suffisant pour un projet de classe :
en production on utiliserait un cache partagé et l'adresse réelle derrière le proxy."""
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse


def rate_limit(name, limit, window):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method == "POST":
                key = f"rl:{name}:{request.META.get('REMOTE_ADDR', '?')}"
                cache.add(key, 0, window)
                try:
                    count = cache.incr(key)
                except ValueError:
                    cache.set(key, 1, window)
                    count = 1
                if count > limit:
                    response = HttpResponse("Trop de requêtes. Réessayez dans une minute.",
                                            status=429, content_type="text/plain; charset=utf-8")
                    response["Retry-After"] = str(window)
                    return response
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
