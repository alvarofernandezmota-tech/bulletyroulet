import random

from bones_bullets.game import HANDS_PER_LEVEL, GameState, Upgrade, level_target
from bones_bullets.hands import HandType
from bones_bullets.revolver import Chamber


def test_three_wounds_is_game_over():
    g = GameState(random.Random(0))
    g.cylinder.live = 6  # solo balas
    g.cylinder.reload(g.rng)
    for _ in range(3):
        assert g.pull_trigger().chamber is Chamber.LIVE
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
    assert Upgrade.SHIELD in list(Upgrade)
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
    assert a.pull_trigger().chamber == b.pull_trigger().chamber
    assert [d.value for d in a.dice] == [d.value for d in b.dice]


def _all_safe(g: GameState) -> None:
    g.cylinder.live = 0
    g.cylinder.reload(g.rng)


def test_streak_adds_multiplier_and_resets_on_play():
    g = GameState(random.Random(0))
    _all_safe(g)
    g.pull_trigger()
    g.pull_trigger()
    assert g.streak == 2
    base = g.mults[g.current_hand().hand]
    assert g.current_hand().mult == base + 1.0
    g.play_hand()
    assert g.streak == 0


def test_shield_absorbs_first_bullet_per_level():
    g = GameState(random.Random(0))
    g.apply_upgrade(Upgrade.SHIELD)
    g.next_level()
    g.cylinder.live = 6
    g.cylinder.reload(g.rng)
    r = g.pull_trigger()
    assert r.shielded and not r.wounded and g.wounds == 0
    r = g.pull_trigger()
    assert r.wounded and g.wounds == 1


def test_extra_hand_and_loaded_die():
    g = GameState(random.Random(0))
    g.apply_upgrade(Upgrade.EXTRA_HAND)
    g.apply_upgrade(Upgrade.LOADED_DIE)
    g.next_level()
    assert g.hands_left == HANDS_PER_LEVEL + 1
    loaded = [d for d in g.dice if d.faces != [1, 2, 3, 4, 5, 6]]
    assert len(loaded) == 1 and min(loaded[0].faces) == 3


def test_bounce_keeps_best_of_two():
    g = GameState(random.Random(1))
    g.cylinder.live = 0
    g.cylinder.bounce = 6
    g.cylinder.reload(g.rng)
    r = g.pull_trigger()
    assert r.chamber is Chamber.BOUNCE and g.streak == 1
