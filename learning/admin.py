from django.contrib import admin

from .models import LessonProgress, Note, StudyDay


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "status", "updated_at")
    list_filter = ("status", "lesson__chapter__course")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("user", "target_label", "updated_at")
    search_fields = ("body_md",)


@admin.register(StudyDay)
class StudyDayAdmin(admin.ModelAdmin):
    list_display = ("user", "date")
    list_filter = ("date",)
