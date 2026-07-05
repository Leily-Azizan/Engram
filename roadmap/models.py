from django.conf import settings
from django.db import models
from django.utils import timezone

from catalog.markdown import render_markdown
from catalog.models import Course


class RoadmapStage(models.Model):
    """One step on the zero-to-hero DevOps path.

    A stage describes *what to learn*, *what to build*, and *when you're done*.
    It may link to courses hosted on this platform (their lesson progress is
    shown on the roadmap) or point at skills practiced outside the app.
    """

    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=200)
    icon = models.CharField(max_length=8, default="🧭", help_text="Emoji for the timeline node")
    tagline = models.CharField(max_length=300, blank=True)
    est_weeks = models.PositiveIntegerField(null=True, blank=True)
    learn_md = models.TextField(blank=True, help_text="What to learn in this stage")
    build_md = models.TextField(blank=True, help_text="Hands-on things to build")
    done_when_md = models.TextField(blank=True, help_text="Self-check: you're done when…")
    courses = models.ManyToManyField(Course, blank=True, related_name="roadmap_stages")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return f"{self.order}. {self.title}"

    @property
    def learn_html(self):
        return render_markdown(self.learn_md)

    @property
    def build_html(self):
        return render_markdown(self.build_md)

    @property
    def done_when_html(self):
        return render_markdown(self.done_when_md)


class StageProgress(models.Model):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    STATUS_CHOICES = [
        (NOT_STARTED, "Not started"),
        (IN_PROGRESS, "In progress"),
        (DONE, "Done"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stage = models.ForeignKey(RoadmapStage, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NOT_STARTED)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "stage")]

    def __str__(self):
        return f"{self.user} · {self.stage} · {self.status}"

    def set_status(self, status):
        self.status = status
        now = timezone.now()
        if status == self.IN_PROGRESS and not self.started_at:
            self.started_at = now
        if status == self.DONE:
            self.completed_at = now
            if not self.started_at:
                self.started_at = now
        if status == self.NOT_STARTED:
            self.started_at = None
            self.completed_at = None
        self.save()
