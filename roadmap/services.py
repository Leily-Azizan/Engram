"""Roadmap helpers: per-stage status rows and the 'you are here' marker."""
from learning.services import course_progress

from .models import RoadmapStage, StageProgress


def roadmap_overview(user):
    """Build the full roadmap view-model for a user.

    Each row carries the stage, its (possibly auto-derived) status, linked
    course progress, and whether it is the *current* stage — the first one
    not yet done, i.e. "you are here".
    """
    stages = RoadmapStage.objects.prefetch_related("courses").order_by("order")
    manual = {p.stage_id: p for p in StageProgress.objects.filter(user=user)}

    rows = []
    for stage in stages:
        progress = manual.get(stage.id)
        status = progress.status if progress else StageProgress.NOT_STARTED
        course_rows = [
            {"course": c, "progress": course_progress(user, c)}
            for c in stage.courses.all()
        ]
        # Auto-detect: studying a linked course means the stage is underway.
        if status == StageProgress.NOT_STARTED and any(
            cr["progress"]["learned"] or cr["progress"]["reading"] for cr in course_rows
        ):
            status = StageProgress.IN_PROGRESS
        rows.append(
            {
                "stage": stage,
                "status": status,
                "courses": course_rows,
                "is_current": False,
            }
        )

    current = None
    for row in rows:
        if row["status"] != StageProgress.DONE:
            row["is_current"] = True
            current = row
            break

    done = sum(1 for r in rows if r["status"] == StageProgress.DONE)
    total = len(rows)
    return {
        "rows": rows,
        "current": current,
        "done": done,
        "total": total,
        "pct": round(100 * done / total) if total else 0,
    }
