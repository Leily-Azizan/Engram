from django.contrib import admin

from .models import (
    FeynmanAttempt,
    FeynmanPrompt,
    Flashcard,
    ReviewLog,
    ReviewState,
)


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ("__str__", "lesson", "card_type")
    list_filter = ("card_type", "lesson__chapter__course")
    search_fields = ("front", "back", "cloze_text")


@admin.register(ReviewState)
class ReviewStateAdmin(admin.ModelAdmin):
    list_display = ("user", "flashcard", "due_date", "interval", "repetitions", "ease_factor")
    list_filter = ("due_date",)


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ("user", "flashcard", "quality", "reviewed_at")


@admin.register(FeynmanPrompt)
class FeynmanPromptAdmin(admin.ModelAdmin):
    list_display = ("__str__", "lesson")
    list_filter = ("lesson__chapter__course",)


@admin.register(FeynmanAttempt)
class FeynmanAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "prompt", "confidence", "created_at")
