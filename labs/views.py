from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from learning.services import record_study
from .models import Lab, LabAttempt


def lab_list(request):
    labs = Lab.objects.select_related("course", "chapter", "lesson")
    attempts = {a.lab_id: a for a in LabAttempt.objects.filter(user=request.user)}
    rows = [{"lab": lab, "attempt": attempts.get(lab.id)} for lab in labs]
    return render(request, "labs/lab_list.html", {"rows": rows})


def lab_detail(request, slug):
    lab = get_object_or_404(Lab, slug=slug)
    attempt, _ = LabAttempt.objects.get_or_create(user=request.user, lab=lab)
    return render(request, "labs/lab_detail.html", {"lab": lab, "attempt": attempt})


@require_POST
def lab_save(request, slug):
    lab = get_object_or_404(Lab, slug=slug)
    attempt, _ = LabAttempt.objects.get_or_create(user=request.user, lab=lab)
    attempt.solution_notes_md = request.POST.get("solution_notes_md", "")
    status = request.POST.get("status")
    if status in dict(LabAttempt.STATUS_CHOICES):
        attempt.status = status
        if status == LabAttempt.DONE and not attempt.completed_at:
            attempt.completed_at = timezone.now()
    rating = request.POST.get("self_rating", "")
    if rating.isdigit():
        attempt.self_rating = int(rating)
    attempt.save()
    record_study(request.user)
    return redirect("lab_detail", slug=slug)
