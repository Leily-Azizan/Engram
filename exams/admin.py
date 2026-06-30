from django.contrib import admin

from .models import (
    AcceptedAnswer,
    AttemptAnswer,
    Choice,
    ExamAttempt,
    Question,
    Quiz,
)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


class AcceptedAnswerInline(admin.TabularInline):
    model = AcceptedAnswer
    extra = 0


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "scope", "course", "chapter", "question_count")
    list_filter = ("scope", "course")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "quiz", "qtype", "points")
    list_filter = ("qtype", "quiz")
    inlines = [ChoiceInline, AcceptedAnswerInline]


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "score", "max_score", "started_at", "finished_at")
    list_filter = ("quiz",)
