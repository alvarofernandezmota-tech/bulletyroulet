import random

import pytest

from bones_bullets.dice import Die
from bones_bullets.hands import BASE_MULT, HandType, evaluate, score


def dice(*values: int) -> list[Die]:
    return [Die(v) for v in values]


@pytest.mark.parametrize(
    "values, expected",
    [
        ((1, 2, 3, 5, 6), HandType.HIGH_CARD),
        ((2, 2, 3, 5, 6), HandType.PAIR),
        ((2, 2, 5, 5, 6), HandType.TWO_PAIR),
        ((4, 4, 4, 1, 6), HandType.THREE_KIND),
        ((1, 2, 3, 4, 5), HandType.STRAIGHT),
        ((6, 5, 4, 3, 2), HandType.STRAIGHT),
        ((3, 3, 3, 5, 5), HandType.FULL_HOUSE),
        ((6, 6, 6, 6, 1), HandType.FOUR_KIND),
        ((2, 2, 2, 2, 2), HandType.FIVE_KIND),
    ],
)
def test_evaluate(values, expected):
    assert evaluate(dice(*values)) == expected


def test_not_straight_with_gap():
    assert evaluate(dice(1, 2, 3, 4, 6)) == HandType.HIGH_CARD


def test_score_sums_all_five_dice():
    hand, total, mult, points = score(dice(2, 2, 3, 5, 6))
    assert hand == HandType.PAIR
    assert total == 18  # incluye los tres dados que no forman la pareja
    assert mult == BASE_MULT[HandType.PAIR]
    assert points == 27


def test_score_uses_custom_mults():
    mults = dict(BASE_MULT)
    mults[HandType.PAIR] += 1
    _, total, mult, points = score(dice(2, 2, 3, 5, 6), mults)
    assert mult == 2.5 and points == 45


def test_all_hand_types_have_multiplier():
    assert set(BASE_MULT) == set(HandType)
