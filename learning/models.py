from django.conf import settings
from django.db import models
from django.utils import timezone

from catalog.markdown import render_markdown
from catalog.models import Chapter, Lesson


class LessonProgress(models.Model):
    NOT_STARTED = "not_started"
    READING = "reading"
    LEARNED = "learned"
    STATUS_CHOICES = [
        (NOT_STARTED, "Not started"),
        (READING, "Reading"),
        (LEARNED, "Learned"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NOT_STARTED)
    read_at = models.DateTimeField(null=True, blank=True)
    learned_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "lesson")]

    def __str__(self):
        return f"{self.user} · {self.lesson} · {self.status}"

    def set_status(self, status):
        self.status = status
        now = timezone.now()
        if status == self.READING and not self.read_at:
            self.read_at = now
        if status == self.LEARNED:
            self.learned_at = now
            if not self.read_at:
                self.read_at = now
        self.save()


class Note(models.Model):
    """The 'My Notes' area attached to a lesson or a chapter."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name="notes"
    )
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, null=True, blank=True, related_name="notes"
    )
    body_md = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Note by {self.user} on {self.target}"

    @property
    def body_html(self):
        return render_markdown(self.body_md)

    @property
    def target(self):
        return self.lesson or self.chapter

    @property
    def target_label(self):
        if self.lesson:
            return f"{self.lesson.chapter.course.name} · {self.lesson.title}"
        if self.chapter:
            return f"{self.chapter.course.name} · {self.chapter.title}"
        return "—"

    @property
    def target_url(self):
        target = self.target
        return target.get_absolute_url() if target else "#"


class StudyDay(models.Model):
    """One row per day the user did any studying — powers streaks."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = [("user", "date")]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} studied on {self.date}"
