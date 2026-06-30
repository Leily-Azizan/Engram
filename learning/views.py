from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Chapter, Course, Lesson
from exams.models import ExamAttempt, Quiz
from labs.models import Lab, LabAttempt
from recall.models import Flashcard
from recall.services import review_counts
from . import services as L
from .models import LessonProgress, Note


def dashboard(request):
    user = request.user
    counts = review_counts(user)

    # Weak topics: quizzes whose most-recent attempt scored below 70%.
    weak = []
    latest_by_quiz = {}
    for attempt in ExamAttempt.objects.filter(user=user, finished_at__isnull=False).select_related("quiz"):
        if attempt.quiz_id not in latest_by_quiz:
            latest_by_quiz[attempt.quiz_id] = attempt
    for attempt in latest_by_quiz.values():
        if attempt.percent < 70:
            weak.append(attempt)
    weak.sort(key=lambda a: a.percent)

    open_labs = (
        LabAttempt.objects.filter(user=user)
        .exclude(status=LabAttempt.DONE)
        .select_related("lab")[:5]
    )

    return render(
        request,
        "learning/dashboard.html",
        {
            "streak": L.current_streak(user),
            "review_counts": counts,
            "courses_progress": L.all_courses_progress(user),
            "next_lesson": L.next_lesson(user),
            "weak_attempts": weak[:5],
            "open_labs": open_labs,
            "recent_attempts": ExamAttempt.objects.filter(
                user=user, finished_at__isnull=False
            ).select_related("quiz")[:5],
            "labs_done": LabAttempt.objects.filter(user=user, status=LabAttempt.DONE).count(),
            "lessons_learned": LessonProgress.objects.filter(
                user=user, status=LessonProgress.LEARNED
            ).count(),
        },
    )


def session(request):
    """Today's interleaved session: reviews + a quiz + a lab + next lesson."""
    user = request.user
    counts = review_counts(user)

    # Pick a quiz the user hasn't attempted yet (else the first quiz).
    attempted_ids = ExamAttempt.objects.filter(user=user).values_list("quiz_id", flat=True)
    quiz = (
        Quiz.objects.exclude(id__in=attempted_ids).order_by("order").first()
        or Quiz.objects.order_by("order").first()
    )

    # Suggest a lab: an open attempt, else a not-yet-attempted lab.
    open_attempt = (
        LabAttempt.objects.filter(user=user)
        .exclude(status=LabAttempt.DONE)
        .select_related("lab")
        .first()
    )
    if open_attempt:
        lab = open_attempt.lab
    else:
        done_ids = LabAttempt.objects.filter(user=user, status=LabAttempt.DONE).values_list(
            "lab_id", flat=True
        )
        lab = Lab.objects.exclude(id__in=done_ids).order_by("order").first()

    return render(
        request,
        "learning/session.html",
        {
            "review_counts": counts,
            "quiz": quiz,
            "lab": lab,
            "next_lesson": L.next_lesson(user),
            "streak": L.current_streak(user),
        },
    )


def notes_all(request):
    query = request.GET.get("q", "").strip()
    notes = Note.objects.filter(user=request.user).select_related(
        "lesson", "lesson__chapter", "lesson__chapter__course", "chapter", "chapter__course"
    )
    if query:
        notes = notes.filter(body_md__icontains=query)
    return render(request, "learning/notes_all.html", {"notes": notes, "query": query})


@require_POST
def note_save(request):
    body_md = request.POST.get("body_md", "").strip()
    lesson_id = request.POST.get("lesson_id")
    chapter_id = request.POST.get("chapter_id")

    if lesson_id:
        target = get_object_or_404(Lesson, id=lesson_id)
        note, _ = Note.objects.get_or_create(user=request.user, lesson=target)
    elif chapter_id:
        target = get_object_or_404(Chapter, id=chapter_id)
        note, _ = Note.objects.get_or_create(user=request.user, chapter=target)
    else:
        return redirect("dashboard")

    note.body_md = body_md
    note.save()
    L.record_study(request.user)
    return redirect(f"{target.get_absolute_url()}#notes")


@require_POST
def progress_update(request):
    lesson = get_object_or_404(Lesson, id=request.POST.get("lesson_id"))
    status = request.POST.get("status")
    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    if status in dict(LessonProgress.STATUS_CHOICES):
        progress.set_status(status)
    L.record_study(request.user)
    return redirect(request.POST.get("next") or lesson.get_absolute_url())


def search(request):
    """Search across lessons, chapters, labs, flashcards, and notes.

    Optional ``course`` GET param scopes the results to a single course (used by
    the in-page search box on the course/lessons pages).
    """
    query = request.GET.get("q", "").strip()
    course_slug = request.GET.get("course", "").strip()
    course = Course.objects.filter(slug=course_slug).first() if course_slug else None

    lessons = chapters = labs = cards = notes = []
    if query:
        lesson_qs = Lesson.objects.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(body_md__icontains=query)
            | Q(deep_dive_md__icontains=query)
        )
        chapter_qs = Chapter.objects.filter(
            Q(title__icontains=query) | Q(summary__icontains=query)
        )
        lab_qs = Lab.objects.filter(
            Q(title__icontains=query)
            | Q(scenario_md__icontains=query)
            | Q(deliverable_md__icontains=query)
            | Q(solution_md__icontains=query)
        )
        card_qs = Flashcard.objects.filter(
            Q(front__icontains=query)
            | Q(back__icontains=query)
            | Q(cloze_text__icontains=query)
        )
        note_qs = Note.objects.filter(user=request.user, body_md__icontains=query)

        if course:
            lesson_qs = lesson_qs.filter(chapter__course=course)
            chapter_qs = chapter_qs.filter(course=course)
            lab_qs = lab_qs.filter(
                Q(course=course)
                | Q(chapter__course=course)
                | Q(lesson__chapter__course=course)
            )
            card_qs = card_qs.filter(lesson__chapter__course=course)
            note_qs = note_qs.filter(
                Q(lesson__chapter__course=course) | Q(chapter__course=course)
            )

        lessons = list(
            lesson_qs.select_related("chapter", "chapter__course")[:50]
        )
        chapters = list(chapter_qs.select_related("course")[:20])
        labs = list(lab_qs[:30])
        cards = list(
            card_qs.select_related(
                "lesson", "lesson__chapter", "lesson__chapter__course"
            )[:30]
        )
        notes = list(
            note_qs.select_related(
                "lesson", "lesson__chapter", "lesson__chapter__course",
                "chapter", "chapter__course",
            )[:30]
        )
    total = len(lessons) + len(chapters) + len(labs) + len(cards) + len(notes)
    return render(
        request,
        "learning/search.html",
        {
            "query": query,
            "course": course,
            "lessons": lessons,
            "chapters": chapters,
            "labs": labs,
            "cards": cards,
            "notes": notes,
            "total": total,
        },
    )
