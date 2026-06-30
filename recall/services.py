"""Helpers for building review queues."""
from django.utils import timezone

from .models import Flashcard, ReviewState

# Quality grades surfaced as buttons in the UI.
GRADE_AGAIN = 1
GRADE_HARD = 3
GRADE_GOOD = 4
GRADE_EASY = 5
GRADES = {
    "again": GRADE_AGAIN,
    "hard": GRADE_HARD,
    "good": GRADE_GOOD,
    "easy": GRADE_EASY,
}


def due_state_ids(user):
    today = timezone.localdate()
    return list(
        ReviewState.objects.filter(user=user, due_date__lte=today).values_list(
            "flashcard_id", flat=True
        )
    )


def new_flashcards(user, lessons=None, limit=20):
    """Cards the user has never reviewed (no ReviewState yet)."""
    seen = ReviewState.objects.filter(user=user).values_list("flashcard_id", flat=True)
    qs = Flashcard.objects.exclude(id__in=seen).select_related(
        "lesson", "lesson__chapter", "lesson__chapter__course"
    )
    if lessons is not None:
        qs = qs.filter(lesson__in=lessons)
    return list(qs[:limit])


def due_flashcards(user, lessons=None):
    """Cards whose ReviewState is due today or earlier."""
    today = timezone.localdate()
    qs = (
        ReviewState.objects.filter(user=user, due_date__lte=today)
        .select_related("flashcard", "flashcard__lesson", "flashcard__lesson__chapter")
        .order_by("due_date")
    )
    cards = [s.flashcard for s in qs]
    if lessons is not None:
        lesson_ids = {l.id for l in lessons}
        cards = [c for c in cards if c.lesson_id in lesson_ids]
    return cards


def next_card(user, lessons=None, max_new=20):
    """Return the next card to review: due cards first, then new ones."""
    due = due_flashcards(user, lessons=lessons)
    if due:
        return due[0]
    new = new_flashcards(user, lessons=lessons, limit=max_new)
    return new[0] if new else None


def review_counts(user):
    today = timezone.localdate()
    due = ReviewState.objects.filter(user=user, due_date__lte=today).count()
    new = len(new_flashcards(user, limit=1000))
    return {"due": due, "new": min(new, 20), "new_total": new}
