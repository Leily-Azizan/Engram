from django.test import TestCase

from exams.models import AcceptedAnswer, Choice, Question, Quiz


class GradingTests(TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.create(title="T", slug="t")

    def test_mcq_grading(self):
        q = Question.objects.create(quiz=self.quiz, qtype=Question.MCQ, text="?")
        right = Choice.objects.create(question=q, text="a", is_correct=True)
        wrong = Choice.objects.create(question=q, text="b")
        self.assertTrue(q.grade(selected_choice_id=right.id))
        self.assertFalse(q.grade(selected_choice_id=wrong.id))
        self.assertFalse(q.grade(selected_choice_id=None))

    def test_fill_in_normalises_whitespace_and_case(self):
        q = Question.objects.create(quiz=self.quiz, qtype=Question.FILL_IN, text="?")
        AcceptedAnswer.objects.create(question=q, value="ls -la")
        self.assertTrue(q.grade(given_text="  LS   -LA "))
        self.assertFalse(q.grade(given_text="ls"))
        self.assertFalse(q.grade(given_text=""))

    def test_command_regex_match(self):
        q = Question.objects.create(quiz=self.quiz, qtype=Question.COMMAND, text="?")
        AcceptedAnswer.objects.create(
            question=q, value="(sudo )?systemctl restart .+", match=AcceptedAnswer.REGEX
        )
        self.assertTrue(q.grade(given_text="sudo systemctl restart nginx"))
        self.assertTrue(q.grade(given_text="systemctl restart sshd"))
        self.assertFalse(q.grade(given_text="systemctl status nginx"))

    def test_multiple_accepted_answers(self):
        q = Question.objects.create(quiz=self.quiz, qtype=Question.COMMAND, text="?")
        AcceptedAnswer.objects.create(question=q, value="ls -la")
        AcceptedAnswer.objects.create(question=q, value="ls -al")
        self.assertTrue(q.grade(given_text="ls -al"))
        self.assertTrue(q.grade(given_text="ls -la"))
