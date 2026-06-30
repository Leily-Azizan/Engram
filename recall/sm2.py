"""SuperMemo-2 (SM-2) spaced-repetition scheduling.

Pure functions, no Django imports, so they are trivially unit-testable.

quality is the recall grade 0-5:
    0-2 = failed (could not recall) -> repetitions reset, see again tomorrow
    3   = correct but hard
    4   = correct
    5   = correct and easy
"""
from dataclasses import dataclass

MIN_EASE = 1.3
DEFAULT_EASE = 2.5


@dataclass(frozen=True)
class SM2Result:
    ease: float
    interval: int          # days until next review
    repetitions: int


def review(quality: int, repetitions: int, ease: float, interval: int) -> SM2Result:
    """Return the next scheduling state given a review grade.

    Implements the canonical SM-2 algorithm.
    """
    if not 0 <= quality <= 5:
        raise ValueError("quality must be between 0 and 5")

    if quality < 3:
        # Failed recall: restart the repetition count, review again tomorrow.
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease)
        repetitions += 1

    # Update the ease factor (clamped so cards never schedule too aggressively).
    ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ease < MIN_EASE:
        ease = MIN_EASE

    return SM2Result(ease=round(ease, 4), interval=interval, repetitions=repetitions)
