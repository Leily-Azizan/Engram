from django.contrib import admin

from .models import Lab, LabAttempt


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "course", "chapter", "est_minutes")
    list_filter = ("difficulty", "course")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(LabAttempt)
class LabAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "lab", "status", "self_rating", "updated_at")
    list_filter = ("status",)
