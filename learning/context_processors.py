from catalog.models import Course


def nav(request):
    """Expose courses to every template for the sidebar nav."""
    if not request.user.is_authenticated:
        return {}
    return {"nav_courses": Course.objects.all()}
