from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from learning.services import record_study
from .models import (
    FeynmanAttempt,
    FeynmanPrompt,
    Flashcard,
    ReviewLog,
    ReviewState,
)
from .services import GRADES, next_card, review_counts


def review(request):
    card = next_card(request.user)
    return render(
        request,
        "recall/review.html",
        {"card": card, "counts": review_counts(request.user)},
    )


@require_POST
def review_answer(request):
    card = get_object_or_404(Flashcard, id=request.POST.get("flashcard_id"))
    quality = GRADES.get(request.POST.get("grade"), 4)
    state, _ = ReviewState.objects.get_or_create(user=request.user, flashcard=card)
    state.apply_review(quality)
    ReviewLog.objects.create(
        user=request.user,
        flashcard=card,
        quality=quality,
        interval_after=state.interval,
    )
    record_study(request.user)
    return redirect("review")


def feynman(request):
    prompts = FeynmanPrompt.objects.select_related(
        "lesson", "lesson__chapter", "lesson__chapter__course"
    )
    featured_id = request.GET.get("prompt")
    if featured_id:
        featured = prompts.filter(id=featured_id).first()
    else:
        attempted = FeynmanAttempt.objects.filter(user=request.user).values_list(
            "prompt_id", flat=True
        )
        featured = prompts.exclude(id__in=attempted).first() or prompts.first()
    attempts = (
        FeynmanAttempt.objects.filter(user=request.user)
        .select_related("prompt", "prompt__lesson")[:10]
    )
    return render(
        request,
        "recall/feynman.html",
        {"prompts": prompts, "featured": featured, "attempts": attempts},
    )


@require_POST
def feynman_save(request):
    prompt = get_object_or_404(FeynmanPrompt, id=request.POST.get("prompt_id"))
    text = request.POST.get("text", "").strip()
    confidence = request.POST.get("confidence", "3")
    if text:
        FeynmanAttempt.objects.create(
            user=request.user,
            prompt=prompt,
            text=text,
            confidence=int(confidence) if confidence.isdigit() else 3,
        )
        record_study(request.user)
    return redirect("feynman")
