from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def hash_groups(value):
    value = str(value)
    return " ".join(value[i:i + 8] for i in range(0, len(value), 8))


@register.filter
def short_hash(value):
    value = str(value)
    return f"{value[:8]}…{value[-8:]}"


@register.simple_tag
def diff_hash(observed, reference):
    """Affiche `observed` par groupes de 8 en surlignant les caractères qui diffèrent."""
    observed, reference = str(observed), str(reference)
    groups = []
    for start in range(0, len(observed), 8):
        out, run = [], []
        for i in range(start, min(start + 8, len(observed))):
            same = i < len(reference) and reference[i] == observed[i]
            if same:
                if run:
                    out.append(f"<mark>{escape(''.join(run))}</mark>")
                    run = []
                out.append(escape(observed[i]))
            else:
                run.append(observed[i])
        if run:
            out.append(f"<mark>{escape(''.join(run))}</mark>")
        groups.append("".join(out))
    return mark_safe(" ".join(groups))


@register.filter
def initials(user):
    name = (user.get_full_name() or user.get_username()).replace("@", " ").replace(".", " ")
    parts = name.split()
    letters = "".join(p[0] for p in parts[:2]) or name[:2]
    return letters.upper()
