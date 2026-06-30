from django.contrib import admin

from .models import Chapter, Course, Example, Lesson


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    prepopulated_fields = {"slug": ("title",)}


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("order", "title", "slug", "est_minutes")
    prepopulated_fields = {"slug": ("title",)}


class ExampleInline(admin.StackedInline):
    model = Example
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("order", "icon", "name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ChapterInline]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "course")
    list_filter = ("course",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "chapter", "est_minutes")
    list_filter = ("chapter__course",)
    search_fields = ("title", "body_md")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ExampleInline]
