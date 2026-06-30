import re

from django.conf import settings
from django.db import models
from django.urls import reverse

from catalog.markdown import render_markdown
from catalog.models import Chapter, Course


class Quiz(models.Model):
    CHAPTER = "chapter"
    COURSE = "course"
    CUMULATIVE = "cumulative"
    SCOPE_CHOICES = [
        (CHAPTER, "Chapter quiz"),
        (COURSE, "Course exam"),
        (CUMULATIVE, "Cumulative exam"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=CHAPTER)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True, related_name="quizzes"
    )
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, null=True, blank=True, related_name="quizzes"
    )
    description = models.TextField(blank=True)
    time_limit_seconds = models.PositiveIntegerField(
        null=True, blank=True, help_text="Leave empty for untimed"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("quiz_detail", args=[self.slug])

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    FILL_IN = "fill_in"
    COMMAND = "command"
    TYPE_CHOICES = [
        (MCQ, "Multiple choice"),
        (TRUE_FALSE, "True / False"),
        (FILL_IN, "Fill in the blank"),
        (COMMAND, "Command recall"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    qtype = models.CharField(max_length=20, choices=TYPE_CHOICES, default=MCQ)
    text = models.TextField()
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:70]

    @property
    def text_html(self):
        return render_markdown(self.text)

    @property
    def explanation_html(self):
        return render_markdown(self.explanation)

    def grade(self, given_text="", selected_choice_id=None):
        """Return True if the supplied answer is correct."""
        if self.qtype in (self.MCQ, self.TRUE_FALSE):
            if not selected_choice_id:
                return False
            return self.choices.filter(id=selected_choice_id, is_correct=True).exists()
        # Text answers (fill-in / command recall)
        candidate = (given_text or "").strip()
        if not candidate:
            return False
        for accepted in self.accepted_answers.all():
            if accepted.matches(candidate):
                return True
        return False


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=400)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class AcceptedAnswer(models.Model):
    EXACT = "exact"        # case-insensitive, whitespace-normalised equality
    REGEX = "regex"
    MATCH_CHOICES = [(EXACT, "Exact (case-insensitive)"), (REGEX, "Regex")]

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="accepted_answers"
    )
    value = models.CharField(max_length=400)
    match = models.CharField(max_length=10, choices=MATCH_CHOICES, default=EXACT)

    def __str__(self):
        return self.value

    def matches(self, candidate):
        candidate = candidate.strip()
        if self.match == self.REGEX:
            try:
                return re.fullmatch(self.value, candidate) is not None
            except re.error:
                return False
        # EXACT: collapse internal whitespace, compare case-insensitively
        norm = lambda s: " ".join(s.split()).lower()
        return norm(candidate) == norm(self.value)


class ExamAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} · {self.quiz} · {self.score}/{self.max_score}"

    @property
    def percent(self):
        return round(100 * self.score / self.max_score) if self.max_score else 0

    @property
    def passed(self):
        return self.percent >= 70


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(
        ExamAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    given_text = models.CharField(max_length=400, blank=True)
    selected_choice = models.ForeignKey(
        Choice, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_correct = models.BooleanField(default=False)
