from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from learning.services import record_study
from .models import RoadmapStage, StageProgress
from .services import roadmap_overview


def roadmap(request):
    return render(request, "roadmap/roadmap.html", roadmap_overview(request.user))


@require_POST
def stage_update(request):
    stage = get_object_or_404(RoadmapStage, id=request.POST.get("stage_id"))
    status = request.POST.get("status")
    progress, _ = StageProgress.objects.get_or_create(user=request.user, stage=stage)
    if status in dict(StageProgress.STATUS_CHOICES):
        progress.set_status(status)
        record_study(request.user)
    return redirect(f"/roadmap/#stage-{stage.slug}")
