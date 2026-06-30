from django.shortcuts import get_object_or_404, render

from learning import services as L
from learning.models import LessonProgress, Note
from .models import Chapter, Course, Lesson


def course_list(request):
    return render(
        request,
        "catalog/course_list.html",
        {"courses_progress": L.all_courses_progress(request.user)},
    )


def course_detail(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    lessons = Lesson.objects.filter(chapter__course=course)
    status_map = L.progress_status_map(request.user, lessons)
    chapter_rows = []
    for chapter in course.chapters.prefetch_related("lessons"):
        ch_lessons = list(chapter.lessons.all())
        learned = sum(1 for l in ch_lessons if status_map.get(l.id) == "learned")
        chapter_rows.append(
            {
                "chapter": chapter,
                "lessons": ch_lessons,
                "learned": learned,
                "total": len(ch_lessons),
                "pct": round(100 * learned / len(ch_lessons)) if ch_lessons else 0,
            }
        )
    return render(
        request,
        "catalog/course_detail.html",
        {
            "course": course,
            "chapter_rows": chapter_rows,
            "progress": L.course_progress(request.user, course),
            "status_map": status_map,
        },
    )


def chapter_detail(request, course_slug, chapter_slug):
    chapter = get_object_or_404(
        Chapter, slug=chapter_slug, course__slug=course_slug
    )
    lessons = list(chapter.lessons.all())
    status_map = L.progress_status_map(request.user, lessons)
    note = Note.objects.filter(user=request.user, chapter=chapter).first()
    return render(
        request,
        "catalog/chapter_detail.html",
        {
            "chapter": chapter,
            "lessons": lessons,
            "status_map": status_map,
            "progress": L.chapter_progress(request.user, chapter),
            "note": note,
            "quizzes": chapter.quizzes.all(),
            "labs": chapter.labs.all(),
        },
    )


def lesson_detail(request, course_slug, chapter_slug, lesson_slug):
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        chapter__slug=chapter_slug,
        chapter__course__slug=course_slug,
    )
    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    note = Note.objects.filter(user=request.user, lesson=lesson).first()

    # Previous / next lesson within the whole course (course order).
    course_lessons = list(
        Lesson.objects.filter(chapter__course=lesson.chapter.course)
        .order_by("chapter__order", "order")
        .values_list("id", flat=True)
    )
    idx = course_lessons.index(lesson.id)
    prev_lesson = (
        Lesson.objects.filter(id=course_lessons[idx - 1]).first() if idx > 0 else None
    )
    next_lesson = (
        Lesson.objects.filter(id=course_lessons[idx + 1]).first()
        if idx + 1 < len(course_lessons)
        else None
    )

    L.record_study(request.user)

    return render(
        request,
        "catalog/lesson_detail.html",
        {
            "lesson": lesson,
            "progress": progress,
            "note": note,
            "examples": lesson.examples.all(),
            "flashcards": lesson.flashcards.all(),
            "labs": lesson.labs.all(),
            "feynman_prompts": lesson.feynman_prompts.all(),
            "quizzes": lesson.chapter.quizzes.all(),
            "prev_lesson": prev_lesson,
            "next_lesson": next_lesson,
        },
    )
