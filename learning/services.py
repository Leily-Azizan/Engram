"""Shared learning helpers: streaks, progress aggregation, study logging."""
from datetime import timedelta

from django.utils import timezone

from catalog.models import Chapter, Course, Lesson
from .models import LessonProgress, StudyDay


def record_study(user):
    """Mark today as a study day for the user (idempotent)."""
    if user.is_authenticated:
        StudyDay.objects.get_or_create(user=user, date=timezone.localdate())


def current_streak(user):
    """Consecutive study days ending today (or yesterday if today not logged yet)."""
    days = set(StudyDay.objects.filter(user=user).values_list("date", flat=True))
    if not days:
        return 0
    today = timezone.localdate()
    cursor = today
    if today not in days:
        cursor = today - timedelta(days=1)
        if cursor not in days:
            return 0
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def progress_status_map(user, lessons):
    """Map lesson_id -> status for the given lessons."""
    qs = LessonProgress.objects.filter(user=user, lesson__in=lessons)
    return {p.lesson_id: p.status for p in qs}


def course_progress(user, course):
    total = Lesson.objects.filter(chapter__course=course).count()
    learned = LessonProgress.objects.filter(
        user=user, lesson__chapter__course=course, status=LessonProgress.LEARNED
    ).count()
    reading = LessonProgress.objects.filter(
        user=user, lesson__chapter__course=course, status=LessonProgress.READING
    ).count()
    pct = round(100 * learned / total) if total else 0
    return {"total": total, "learned": learned, "reading": reading, "pct": pct}


def chapter_progress(user, chapter):
    total = chapter.lessons.count()
    learned = LessonProgress.objects.filter(
        user=user, lesson__chapter=chapter, status=LessonProgress.LEARNED
    ).count()
    pct = round(100 * learned / total) if total else 0
    return {"total": total, "learned": learned, "pct": pct}


def next_lesson(user):
    """First not-yet-learned lesson in course/chapter/lesson order — 'what to study next'."""
    learned_ids = LessonProgress.objects.filter(
        user=user, status=LessonProgress.LEARNED
    ).values_list("lesson_id", flat=True)
    return (
        Lesson.objects.exclude(id__in=learned_ids)
        .select_related("chapter", "chapter__course")
        .order_by("chapter__course__order", "chapter__order", "order")
        .first()
    )


def all_courses_progress(user):
    return [
        {"course": c, "progress": course_progress(user, c)}
        for c in Course.objects.all()
    ]
