from django.db import models
from django.urls import reverse

from .markdown import render_markdown


class Course(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    icon = models.CharField(max_length=8, default="📘", help_text="Emoji shown in nav")
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("course_detail", args=[self.slug])

    @property
    def description_html(self):
        return render_markdown(self.description)


class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    summary = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]
        unique_together = [("course", "slug")]

    def __str__(self):
        return f"{self.course.name} · {self.title}"

    def get_absolute_url(self):
        return reverse("chapter_detail", args=[self.course.slug, self.slug])

    @property
    def summary_html(self):
        return render_markdown(self.summary)


class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    summary = models.CharField(max_length=400, blank=True)
    body_md = models.TextField(blank=True)
    deep_dive_md = models.TextField(
        blank=True, help_text="Optional 'Under the hood' OS-level deep dive"
    )
    est_minutes = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]
        unique_together = [("chapter", "slug")]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "lesson_detail",
            args=[self.chapter.course.slug, self.chapter.slug, self.slug],
        )

    @property
    def body_html(self):
        return render_markdown(self.body_md)

    @property
    def deep_dive_html(self):
        return render_markdown(self.deep_dive_md)

    @property
    def course(self):
        return self.chapter.course


class Example(models.Model):
    """Optional structured worked example (most examples live inline in body_md)."""

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="examples")
    title = models.CharField(max_length=200)
    language = models.CharField(max_length=30, default="bash")
    code = models.TextField()
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

    @property
    def explanation_html(self):
        return render_markdown(self.explanation)
