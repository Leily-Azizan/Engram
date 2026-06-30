import re
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from catalog.markdown import render_markdown
from catalog.models import Lesson
from . import sm2

CLOZE_RE = re.compile(r"\{\{c\d+::(.*?)\}\}")


class Flashcard(models.Model):
    BASIC = "basic"
    CLOZE = "cloze"
    TYPE_CHOICES = [(BASIC, "Basic (front/back)"), (CLOZE, "Cloze deletion")]

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="flashcards"
    )
    card_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=BASIC)
    front = models.TextField(blank=True)
    back = models.TextField(blank=True)
    cloze_text = models.TextField(
        blank=True, help_text="Use {{c1::hidden answer}} syntax for cloze cards"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["lesson", "order"]

    def __str__(self):
        return (self.front or self.cloze_text)[:60]

    @property
    def prompt_html(self):
        if self.card_type == self.CLOZE:
            return render_markdown(CLOZE_RE.sub("**[ … ]**", self.cloze_text))
        return render_markdown(self.front)

    @property
    def answer_html(self):
        if self.card_type == self.CLOZE:
            return render_markdown(CLOZE_RE.sub(lambda m: f"**{m.group(1)}**", self.cloze_text))
        return render_markdown(self.back)


class ReviewState(models.Model):
    """Per-user SM-2 scheduling state for a flashcard."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    flashcard = models.ForeignKey(
        Flashcard, on_delete=models.CASCADE, related_name="states"
    )
    ease_factor = models.FloatField(default=sm2.DEFAULT_EASE)
    interval = models.PositiveIntegerField(default=0)
    repetitions = models.PositiveIntegerField(default=0)
    due_date = models.DateField(default=timezone.localdate)
    last_reviewed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "flashcard")]
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.user} · {self.flashcard} · due {self.due_date}"

    def apply_review(self, quality):
        result = sm2.review(
            quality=quality,
            repetitions=self.repetitions,
            ease=self.ease_factor,
            interval=self.interval,
        )
        self.ease_factor = result.ease
        self.interval = result.interval
        self.repetitions = result.repetitions
        self.last_reviewed = timezone.now()
        self.due_date = timezone.localdate() + timedelta(days=result.interval)
        self.save()
        return result


class ReviewLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE)
    quality = models.PositiveSmallIntegerField()
    interval_after = models.PositiveIntegerField(default=0)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reviewed_at"]


class FeynmanPrompt(models.Model):
    """An 'explain it back in your own words' prompt for a lesson."""

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="feynman_prompts"
    )
    prompt = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["lesson", "order"]

    def __str__(self):
        return self.prompt[:70]


class FeynmanAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prompt = models.ForeignKey(
        FeynmanPrompt, on_delete=models.CASCADE, related_name="attempts"
    )
    text = models.TextField()
    confidence = models.PositiveSmallIntegerField(default=3)  # 1-5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def text_html(self):
        return render_markdown(self.text)
