from django.conf import settings
from django.db import models
from django.urls import reverse

from catalog.markdown import render_markdown
from catalog.models import Chapter, Course, Lesson


class Lab(models.Model):
    """A hands-on engineering mini-project that makes you reason, not just recall."""

    INTRO = "intro"
    CORE = "core"
    CHALLENGE = "challenge"
    DIFFICULTY_CHOICES = [
        (INTRO, "Intro"),
        (CORE, "Core"),
        (CHALLENGE, "Challenge"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True, related_name="labs"
    )
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, null=True, blank=True, related_name="labs"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name="labs"
    )
    difficulty = models.CharField(max_length=12, choices=DIFFICULTY_CHOICES, default=CORE)
    est_minutes = models.PositiveIntegerField(default=20)
    scenario_md = models.TextField(help_text="The situation / problem to solve")
    deliverable_md = models.TextField(help_text="What you must produce / demonstrate")
    hints_md = models.TextField(blank=True)
    solution_md = models.TextField(blank=True, help_text="Revealed after attempting")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("lab_detail", args=[self.slug])

    @property
    def scenario_html(self):
        return render_markdown(self.scenario_md)

    @property
    def deliverable_html(self):
        return render_markdown(self.deliverable_md)

    @property
    def hints_html(self):
        return render_markdown(self.hints_md)

    @property
    def solution_html(self):
        return render_markdown(self.solution_md)

    @property
    def course_obj(self):
        if self.course:
            return self.course
        if self.chapter:
            return self.chapter.course
        if self.lesson:
            return self.lesson.chapter.course
        return None


class LabAttempt(models.Model):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    STATUS_CHOICES = [
        (TODO, "To do"),
        (IN_PROGRESS, "In progress"),
        (DONE, "Done"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="attempts")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=TODO)
    solution_notes_md = models.TextField(blank=True)
    self_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "lab")]

    def __str__(self):
        return f"{self.user} · {self.lab} · {self.status}"

    @property
    def solution_notes_html(self):
        return render_markdown(self.solution_notes_md)
