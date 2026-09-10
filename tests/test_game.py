import random

from bones_bullets.game import HANDS_PER_LEVEL, GameState, Upgrade, level_target
from bones_bullets.hands import HandType
from bones_bullets.revolver import Chamber


def test_three_wounds_is_game_over():
    g = GameState(random.Random(0))
    g.cylinder.live = 6  # solo balas
    g.cylinder.reload(g.rng)
    for _ in range(3):
        assert g.pull_trigger() is Chamber.LIVE
    assert g.wounds == 3
    assert g.game_over()


def test_bang_consumes_hand_and_scores_zero():
    g = GameState(random.Random(0))
    g.cylinder.live = 6
    g.cylinder.reload(g.rng)
    g.pull_trigger()
    assert g.score == 0 and g.hands_left == HANDS_PER_LEVEL - 1


def test_three_hands_without_target_is_game_over():
    g = GameState(random.Random(0))
    for d in g.dice:
        d.value = 1  # 5 unos = repóker 5*12 = 60 < 69 (nivel 1)
    g.mults[HandType.FIVE_KIND] = 1  # fuerza puntuaciones bajas
    for _ in range(HANDS_PER_LEVEL):
        for d in g.dice:
            d.value = 1
        g.play_hand()
    assert g.score < g.target
    assert g.game_over()


def test_clearing_level_offers_upgrades_and_next_level_resets():
    g = GameState(random.Random(0))
    assert g.target == level_target(1) == 69
    for d in g.dice:
        d.value = 6  # repóker 30*12 = 360
    g.play_hand()
    assert g.level_cleared()
    assert len(g.pending_upgrades) == 3
    assert Upgrade.HEAL not in g.pending_upgrades  # sin heridas no se ofrece
    g.apply_upgrade(Upgrade.MULT_PAIR)
    assert g.mults[HandType.PAIR] == 2.5
    g.next_level()
    assert g.level == 2 and g.score == 0 and g.hands_left == HANDS_PER_LEVEL
    assert g.cylinder.known()["remaining"] == 6
    assert not g.pulled_this_level


def test_cold_blood_heals():
    g = GameState(random.Random(0))
    g.wounds = 1
    for d in g.dice:
        d.value = 6
    g.play_hand()
    assert g.wounds == 0


def test_silver_triples_hand():
    g = GameState(random.Random(0))
    g.silver_active = True
    base = g.current_hand()
    assert base.mult == g.mults[base.hand] * 3


def test_seed_reproducible():
    a, b = GameState(random.Random(7)), GameState(random.Random(7))
    assert [d.value for d in a.dice] == [d.value for d in b.dice]
    assert a.pull_trigger() == b.pull_trigger()
    assert [d.value for d in a.dice] == [d.value for d in b.dice]
