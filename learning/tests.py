from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from catalog.models import Lesson
from exams.models import ExamAttempt, Quiz, Question
from labs.models import Lab, LabAttempt
from learning.models import LessonProgress, Note, StudyDay
from recall.models import Flashcard, ReviewState


class IntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Loading real content also exercises the seed_content command.
        call_command("seed_content", verbosity=0)

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("tester", password="pw")
        self.client.force_login(self.user)

    def test_seed_loaded_content(self):
        self.assertGreater(Lesson.objects.count(), 0)
        self.assertGreater(Flashcard.objects.count(), 0)
        self.assertGreater(Quiz.objects.count(), 0)
        self.assertGreater(Lab.objects.count(), 0)

    def test_core_pages_render(self):
        for url in ["/", "/session/", "/review/", "/review/feynman/",
                    "/exams/", "/labs/", "/notes/", "/courses/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_all_lessons_render(self):
        for lesson in Lesson.objects.all():
            with self.subTest(lesson=lesson.slug):
                self.assertEqual(self.client.get(lesson.get_absolute_url()).status_code, 200)

    def test_progress_and_studyday(self):
        lesson = Lesson.objects.first()
        self.client.post("/progress/update/", {"lesson_id": lesson.id, "status": "learned"})
        self.assertEqual(
            LessonProgress.objects.get(user=self.user, lesson=lesson).status, "learned"
        )
        self.assertTrue(StudyDay.objects.filter(user=self.user).exists())

    def test_note_save(self):
        lesson = Lesson.objects.first()
        self.client.post("/notes/save/", {"lesson_id": lesson.id, "body_md": "**hi**"})
        note = Note.objects.get(user=self.user, lesson=lesson)
        self.assertIn("hi", note.body_md)
        self.assertIn("<strong>hi</strong>", note.body_html)

    def test_review_updates_schedule(self):
        card = Flashcard.objects.first()
        self.client.post("/review/answer/", {"flashcard_id": card.id, "grade": "good"})
        state = ReviewState.objects.get(user=self.user, flashcard=card)
        self.assertEqual(state.interval, 1)
        self.assertEqual(state.repetitions, 1)

    def test_quiz_submit_scores_and_records(self):
        quiz = Quiz.objects.filter(questions__isnull=False).distinct().first()
        data = {}
        for q in quiz.questions.all():
            if q.qtype in (Question.MCQ, Question.TRUE_FALSE):
                correct = q.choices.filter(is_correct=True).first()
                if correct:
                    data[f"q_{q.id}"] = correct.id
            else:
                ans = q.accepted_answers.exclude(match="regex").first()
                if ans:
                    data[f"q_{q.id}"] = ans.value
        resp = self.client.post(f"/exams/{quiz.slug}/submit/", data)
        self.assertEqual(resp.status_code, 302)
        attempt = ExamAttempt.objects.filter(user=self.user, quiz=quiz).latest("started_at")
        self.assertGreater(attempt.score, 0)
        self.assertEqual(self.client.get(f"/exams/attempt/{attempt.id}/").status_code, 200)

    def test_lab_save(self):
        lab = Lab.objects.first()
        self.client.post(
            f"/labs/{lab.slug}/save/",
            {"solution_notes_md": "did it", "status": "done", "self_rating": "4"},
        )
        attempt = LabAttempt.objects.get(user=self.user, lab=lab)
        self.assertEqual(attempt.status, "done")
        self.assertEqual(attempt.self_rating, 4)
        self.assertIsNotNone(attempt.completed_at)

    def test_search_finds_content(self):
        self.assertEqual(self.client.get("/search/").status_code, 200)  # empty query ok
        resp = self.client.get("/search/", {"q": "subnetting"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Lessons")  # a lesson group should appear
        # A command term should resolve too.
        self.assertEqual(self.client.get("/search/", {"q": "chmod"}).status_code, 200)

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)
