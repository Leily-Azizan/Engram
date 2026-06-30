from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from learning.services import record_study
from .models import AttemptAnswer, ExamAttempt, Question, Quiz


def quiz_list(request):
    quizzes = Quiz.objects.select_related("course", "chapter")
    best = {}
    for attempt in ExamAttempt.objects.filter(user=request.user, finished_at__isnull=False):
        if attempt.quiz_id not in best or attempt.percent > best[attempt.quiz_id]:
            best[attempt.quiz_id] = attempt.percent
    return render(request, "exams/quiz_list.html", {"quizzes": quizzes, "best": best})


def quiz_detail(request, slug):
    quiz = get_object_or_404(Quiz, slug=slug)
    attempts = ExamAttempt.objects.filter(
        user=request.user, quiz=quiz, finished_at__isnull=False
    )
    return render(
        request, "exams/quiz_detail.html", {"quiz": quiz, "attempts": attempts}
    )


def quiz_take(request, slug):
    quiz = get_object_or_404(Quiz, slug=slug)
    questions = quiz.questions.prefetch_related("choices")
    return render(
        request, "exams/quiz_take.html", {"quiz": quiz, "questions": questions}
    )


@require_POST
def quiz_submit(request, slug):
    quiz = get_object_or_404(Quiz, slug=slug)
    questions = list(quiz.questions.prefetch_related("choices", "accepted_answers"))
    attempt = ExamAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        max_score=sum(q.points for q in questions),
    )
    score = 0
    for q in questions:
        raw = (request.POST.get(f"q_{q.id}", "") or "").strip()
        if q.qtype in (Question.MCQ, Question.TRUE_FALSE):
            choice_id = int(raw) if raw.isdigit() else None
            is_correct = q.grade(selected_choice_id=choice_id)
            AttemptAnswer.objects.create(
                attempt=attempt,
                question=q,
                selected_choice_id=choice_id,
                is_correct=is_correct,
            )
        else:
            is_correct = q.grade(given_text=raw)
            AttemptAnswer.objects.create(
                attempt=attempt, question=q, given_text=raw, is_correct=is_correct
            )
        if is_correct:
            score += q.points
    attempt.score = score
    attempt.finished_at = timezone.now()
    attempt.save()
    record_study(request.user)
    return redirect("attempt_detail", attempt_id=attempt.id)


def attempt_detail(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    answers = attempt.answers.select_related("question", "selected_choice").prefetch_related(
        "question__choices", "question__accepted_answers"
    )
    return render(
        request, "exams/attempt_detail.html", {"attempt": attempt, "answers": answers}
    )
