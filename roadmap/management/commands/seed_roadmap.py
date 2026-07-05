"""Load the DevOps roadmap from ``content/roadmap.yaml`` into the database.

Idempotent: stages upsert by slug, so editing the YAML and re-running updates
rows in place and preserves per-stage progress. ``seed_content`` runs this
automatically when the file exists.
"""
from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Course
from roadmap.models import RoadmapStage


class Command(BaseCommand):
    help = "Load/refresh the DevOps roadmap from content/roadmap.yaml (upsert by slug)."

    def handle(self, *args, **options):
        path = Path(settings.CONTENT_DIR) / "roadmap.yaml"
        if not path.exists():
            raise CommandError(f"Roadmap file not found: {path}")

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        stages = data.get("stages", [])
        for order, d in enumerate(stages, start=1):
            stage, _ = RoadmapStage.objects.update_or_create(
                slug=d["slug"],
                defaults={
                    "title": d.get("title", d["slug"]),
                    "icon": d.get("icon", "🧭"),
                    "tagline": d.get("tagline", ""),
                    "est_weeks": d.get("est_weeks"),
                    "learn_md": d.get("learn", ""),
                    "build_md": d.get("build", ""),
                    "done_when_md": d.get("done_when", ""),
                    "order": d.get("order", order),
                },
            )
            course_slugs = d.get("courses", [])
            stage.courses.set(Course.objects.filter(slug__in=course_slugs))
            missing = set(course_slugs) - set(
                stage.courses.values_list("slug", flat=True)
            )
            for slug in sorted(missing):
                self.stdout.write(
                    self.style.WARNING(f"  Stage {stage.slug}: unknown course '{slug}'")
                )
        # Stages removed from the YAML disappear from the path.
        RoadmapStage.objects.exclude(slug__in=[d["slug"] for d in stages]).delete()
        self.stdout.write(self.style.SUCCESS(f"Roadmap: {len(stages)} stages loaded."))
