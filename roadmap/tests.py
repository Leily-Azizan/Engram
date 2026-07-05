from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils.html import escape

from catalog.models import Course
from learning.models import LessonProgress, StudyDay
from .models import RoadmapStage, StageProgress
from .services import roadmap_overview


class RoadmapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # seed_content also seeds the roadmap from content/roadmap.yaml.
        call_command("seed_content", verbosity=0)

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("tester", password="pw")
        self.client.force_login(self.user)

    def test_seed_loaded_stages(self):
        self.assertGreater(RoadmapStage.objects.count(), 0)
        # Stages link to real platform courses.
        linux = RoadmapStage.objects.get(slug="linux")
        self.assertIn("lpic-1", linux.courses.values_list("slug", flat=True))
        # Orders are sequential from the YAML list.
        orders = list(RoadmapStage.objects.values_list("order", flat=True))
        self.assertEqual(orders, sorted(orders))

    def test_seed_is_idempotent(self):
        before = RoadmapStage.objects.count()
        call_command("seed_roadmap", verbosity=0)
        self.assertEqual(RoadmapStage.objects.count(), before)

    def test_page_renders_with_current_marker(self):
        resp = self.client.get("/roadmap/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "You are here")
        first = RoadmapStage.objects.order_by("order").first()
        self.assertContains(resp, escape(first.title))

    def test_stage_update_flow(self):
        stage = RoadmapStage.objects.order_by("order").first()
        self.client.post("/roadmap/stage/update/", {"stage_id": stage.id, "status": "in_progress"})
        progress = StageProgress.objects.get(user=self.user, stage=stage)
        self.assertEqual(progress.status, "in_progress")
        self.assertIsNotNone(progress.started_at)

        self.client.post("/roadmap/stage/update/", {"stage_id": stage.id, "status": "done"})
        progress.refresh_from_db()
        self.assertEqual(progress.status, "done")
        self.assertIsNotNone(progress.completed_at)
        # Marking roadmap progress counts as studying.
        self.assertTrue(StudyDay.objects.filter(user=self.user).exists())

    def test_current_advances_after_done(self):
        stages = list(RoadmapStage.objects.order_by("order"))
        overview = roadmap_overview(self.user)
        self.assertEqual(overview["current"]["stage"], stages[0])

        self.client.post("/roadmap/stage/update/", {"stage_id": stages[0].id, "status": "done"})
        overview = roadmap_overview(self.user)
        self.assertEqual(overview["current"]["stage"], stages[1])
        self.assertEqual(overview["done"], 1)

    def test_linked_course_progress_autodetects_in_progress(self):
        stage = RoadmapStage.objects.get(slug="linux")
        lesson = stage.courses.first().chapters.first().lessons.first()
        LessonProgress.objects.create(
            user=self.user, lesson=lesson, status=LessonProgress.LEARNED
        )
        overview = roadmap_overview(self.user)
        row = next(r for r in overview["rows"] if r["stage"] == stage)
        self.assertEqual(row["status"], StageProgress.IN_PROGRESS)

    def test_dashboard_shows_roadmap_position(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "DevOps roadmap")
        self.assertContains(resp, "You are here")
