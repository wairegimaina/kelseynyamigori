from django import template

register = template.Library()


@register.filter
def humanize_count(value):
    """
    Formats a raw integer follower/like/view count into a short display
    string, e.g. 700000 -> '700K+', 1250000 -> '1.3M+', 950 -> '950+'.

    This reads straight from the real numeric field (followers_count) so the
    "By Platform" list never depends on a separate manually-typed string
    that can be left blank.
    """
    try:
        n = int(value or 0)
    except (TypeError, ValueError):
        return value

    if n >= 1_000_000:
        val = n / 1_000_000
        text = f"{val:.1f}".rstrip("0").rstrip(".")
        return f"{text}M+"
    if n >= 1_000:
        val = n / 1_000
        text = f"{val:.1f}".rstrip("0").rstrip(".")
        return f"{text}K+"
    return f"{n}+"
