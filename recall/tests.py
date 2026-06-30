from django.test import TestCase

from recall import sm2


class SM2Tests(TestCase):
    def test_first_correct_review_schedules_one_day(self):
        r = sm2.review(quality=5, repetitions=0, ease=2.5, interval=0)
        self.assertEqual(r.interval, 1)
        self.assertEqual(r.repetitions, 1)

    def test_second_correct_review_schedules_six_days(self):
        r = sm2.review(quality=4, repetitions=1, ease=2.5, interval=1)
        self.assertEqual(r.interval, 6)
        self.assertEqual(r.repetitions, 2)

    def test_third_review_multiplies_by_ease(self):
        r = sm2.review(quality=4, repetitions=2, ease=2.5, interval=6)
        self.assertEqual(r.interval, round(6 * 2.5))
        self.assertEqual(r.repetitions, 3)

    def test_failed_review_resets_repetitions(self):
        r = sm2.review(quality=1, repetitions=5, ease=2.6, interval=30)
        self.assertEqual(r.repetitions, 0)
        self.assertEqual(r.interval, 1)

    def test_ease_never_drops_below_floor(self):
        ease = 2.5
        for _ in range(20):
            ease = sm2.review(quality=0, repetitions=0, ease=ease, interval=0).ease
        self.assertGreaterEqual(ease, sm2.MIN_EASE)

    def test_easy_answer_raises_ease(self):
        r = sm2.review(quality=5, repetitions=2, ease=2.5, interval=6)
        self.assertGreater(r.ease, 2.5)

    def test_invalid_quality_raises(self):
        with self.assertRaises(ValueError):
            sm2.review(quality=6, repetitions=0, ease=2.5, interval=0)
