from django.contrib import admin

from .models import RoadmapStage, StageProgress


@admin.register(RoadmapStage)
class RoadmapStageAdmin(admin.ModelAdmin):
    list_display = ["order", "title", "slug", "est_weeks"]
    list_display_links = ["title"]
    prepopulated_fields = {"slug": ["title"]}
    filter_horizontal = ["courses"]


@admin.register(StageProgress)
class StageProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "stage", "status", "started_at", "completed_at"]
    list_filter = ["status"]
