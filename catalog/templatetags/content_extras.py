from django import template
from django.utils.safestring import mark_safe

from catalog.markdown import render_markdown

register = template.Library()


@register.filter
def markdownify(text):
    return mark_safe(render_markdown(text))


@register.filter
def get_item(mapping, key):
    """Dict lookup by variable key in templates: {{ mymap|get_item:obj.id }}."""
    if mapping is None:
        return None
    return mapping.get(key)


@register.filter
def status_label(status):
    return {
        "not_started": "Not started",
        "reading": "Reading",
        "learned": "Learned",
    }.get(status, "Not started")


@register.filter
def status_color(status):
    return {
        "not_started": "slate",
        "reading": "amber",
        "learned": "emerald",
    }.get(status, "slate")
