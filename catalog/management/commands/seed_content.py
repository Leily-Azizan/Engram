"""Load course content from the ``content/`` tree into the database.

Idempotent: re-running upserts by slug / position, so editing a YAML file and
re-running ``python manage.py seed_content`` updates existing rows in place and
preserves your review history and progress where possible.

Layout::

    content/<course-slug>/course.yaml         # course metadata
    content/<course-slug>/NN-<chapter>.yaml    # one file per chapter (everything)

See content/README.md for the full schema.
"""
from pathlib import Path

import yaml
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Chapter, Course, Lesson
from exams.models import AcceptedAnswer, Choice, Question, Quiz
from labs.models import Lab
from recall.models import FeynmanPrompt, Flashcard


class Command(BaseCommand):
    help = "Load/refresh course content from the content/ directory (upsert by slug)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--course",
            help="Only load this course slug (directory name).",
            default=None,
        )

    def handle(self, *args, **options):
        base = Path(settings.CONTENT_DIR)
        if not base.exists():
            raise CommandError(f"Content directory not found: {base}")

        only = options.get("course")
        course_dirs = sorted(p for p in base.iterdir() if p.is_dir())
        if not course_dirs:
            self.stdout.write(self.style.WARNING("No course directories found."))
            return

        for course_dir in course_dirs:
            if only and course_dir.name != only:
                continue
            self._load_course(course_dir)

        # The DevOps roadmap lives alongside the courses; keep it in sync too.
        if only is None and (base / "roadmap.yaml").exists():
            call_command("seed_roadmap", verbosity=options.get("verbosity", 1))

        self.stdout.write(self.style.SUCCESS("Done."))

    # -- loaders -------------------------------------------------------------
    def _load_course(self, course_dir):
        meta_file = course_dir / "course.yaml"
        if not meta_file.exists():
            self.stdout.write(self.style.WARNING(f"Skip {course_dir.name}: no course.yaml"))
            return
        meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        course, _ = Course.objects.update_or_create(
            slug=meta["slug"],
            defaults={
                "name": meta.get("name", meta["slug"]),
                "icon": meta.get("icon", "📘"),
                "order": meta.get("order", 0),
                "description": meta.get("description", ""),
            },
        )
        self.stdout.write(self.style.MIGRATE_HEADING(f"Course: {course.name}"))

        for chap_file in sorted(course_dir.glob("[0-9]*.y*ml")):
            self._load_chapter(course, chap_file)

    def _load_chapter(self, course, chap_file):
        data = yaml.safe_load(chap_file.read_text(encoding="utf-8")) or {}
        meta = data.get("chapter", {})
        chapter, _ = Chapter.objects.update_or_create(
            course=course,
            slug=meta["slug"],
            defaults={
                "title": meta.get("title", meta["slug"]),
                "summary": meta.get("summary", ""),
                "order": meta.get("order", 0),
            },
        )
        self.stdout.write(f"  Chapter: {chapter.title}")

        for li, lesson_data in enumerate(data.get("lessons", []), start=1):
            self._load_lesson(chapter, course, lesson_data, li)

        if data.get("quiz"):
            self._load_quiz(course, chapter, data["quiz"])
        for lab_data in data.get("labs", []):
            self._load_lab(lab_data, course=course, chapter=chapter)

    def _load_lesson(self, chapter, course, d, default_order):
        lesson, _ = Lesson.objects.update_or_create(
            chapter=chapter,
            slug=d["slug"],
            defaults={
                "title": d.get("title", d["slug"]),
                "summary": d.get("summary", ""),
                "body_md": d.get("body", ""),
                "deep_dive_md": d.get("deep_dive", ""),
                "est_minutes": d.get("est_minutes", 10),
                "order": d.get("order", default_order),
            },
        )

        # Flashcards — upsert by (lesson, order) so ReviewState survives re-seeds.
        cards = d.get("cards", [])
        for ci, card in enumerate(cards):
            if "cloze" in card:
                defaults = {
                    "card_type": Flashcard.CLOZE,
                    "cloze_text": card["cloze"],
                    "front": "",
                    "back": "",
                }
            else:
                defaults = {
                    "card_type": Flashcard.BASIC,
                    "front": card.get("front", ""),
                    "back": card.get("back", ""),
                    "cloze_text": "",
                }
            Flashcard.objects.update_or_create(
                lesson=lesson, order=ci, defaults=defaults
            )
        lesson.flashcards.filter(order__gte=len(cards)).delete()

        # Feynman prompts — upsert by (lesson, order).
        prompts = d.get("feynman", [])
        for fi, text in enumerate(prompts):
            FeynmanPrompt.objects.update_or_create(
                lesson=lesson, order=fi, defaults={"prompt": text}
            )
        lesson.feynman_prompts.filter(order__gte=len(prompts)).delete()

        for lab_data in d.get("labs", []):
            self._load_lab(lab_data, course=course, chapter=chapter, lesson=lesson)

    def _load_lab(self, d, course=None, chapter=None, lesson=None):
        Lab.objects.update_or_create(
            slug=d["slug"],
            defaults={
                "title": d.get("title", d["slug"]),
                "course": course,
                "chapter": chapter,
                "lesson": lesson,
                "difficulty": d.get("difficulty", Lab.CORE),
                "est_minutes": d.get("est_minutes", 20),
                "scenario_md": d.get("scenario", ""),
                "deliverable_md": d.get("deliverable", ""),
                "hints_md": d.get("hints", ""),
                "solution_md": d.get("solution", ""),
                "order": d.get("order", 0),
            },
        )

    def _load_quiz(self, course, chapter, d):
        quiz, _ = Quiz.objects.update_or_create(
            slug=d["slug"],
            defaults={
                "title": d.get("title", d["slug"]),
                "scope": d.get("scope", Quiz.CHAPTER),
                "course": course,
                "chapter": chapter,
                "description": d.get("description", ""),
                "time_limit_seconds": d.get("time_limit_seconds"),
                "order": d.get("order", 0),
            },
        )
        # Rebuild questions for a clean, correct state on every load.
        quiz.questions.all().delete()
        for qi, q in enumerate(d.get("questions", [])):
            question = Question.objects.create(
                quiz=quiz,
                qtype=q.get("type", Question.MCQ),
                text=q.get("text", ""),
                explanation=q.get("explanation", ""),
                points=q.get("points", 1),
                order=qi,
            )
            for chi, ch in enumerate(q.get("choices", [])):
                Choice.objects.create(
                    question=question,
                    text=ch["text"],
                    is_correct=ch.get("correct", False),
                    order=chi,
                )
            for ans in q.get("answers", []):
                if isinstance(ans, dict):
                    AcceptedAnswer.objects.create(
                        question=question,
                        value=ans["value"],
                        match=ans.get("match", AcceptedAnswer.EXACT),
                    )
                else:
                    AcceptedAnswer.objects.create(question=question, value=ans)
