import random

from bones_bullets.ai import PERSONALITIES, make_duel, take_turn
from bones_bullets.duel import new_duel
from bones_bullets.game import MAX_WOUNDS


def test_round_resolves_and_loser_bleeds():
    d = new_duel(random.Random(0))
    me, rival = d.players
    for x in me.dice:
        x.value = 6
    d.play_hand()
    assert d.current is rival
    for x in rival.dice:
        x.value = 1
    rival.dice[0].value = 2
    d.play_hand()
    assert rival.wounds == 1 and me.wounds == 0
    assert d.round == 2 and d.current is rival  # empieza el perdedor


def test_bang_wounds_and_scores_zero():
    d = new_duel(random.Random(0))
    d.cylinder.live = 6
    d.cylinder.reload(d.rng)
    r = d.pull_trigger()
    assert r.wounded and d.players[0].wounds == 1 and d.players[0].played.points == 0
    assert d.current is d.players[1]


def test_bang_loser_does_not_bleed_twice():
    d = new_duel(random.Random(0))
    d.cylinder.live = 6
    d.cylinder.reload(d.rng)
    d.pull_trigger()  # yo: BANG, herida 1, mano 0
    d.play_hand()  # rival juega y gana la ronda
    assert d.players[0].wounds == 1
    assert d.round == 2 and d.current is d.players[0]


def test_three_wounds_ends_duel():
    d = new_duel(random.Random(0))
    d.players[1].wounds = MAX_WOUNDS
    assert d.game_over() and d.winner() is d.players[0]


def test_ai_plays_a_full_turn():
    d = new_duel(random.Random(3))
    d.turn = 1
    events = take_turn(d, PERSONALITIES["tahur"])
    assert events and events[-1]["type"] in ("play", "fire")
    assert d.players[1].played is not None


def test_full_ai_vs_ai_duel_terminates():
    d = new_duel(random.Random(5))
    d.players[0].is_ai = True
    for _ in range(200):
        if d.game_over():
            break
        take_turn(d, PERSONALITIES["loco"] if d.turn else PERSONALITIES["cauto"])
    assert d.game_over()


def test_sheriff_has_four_lives_and_three_bullets():
    d = make_duel(random.Random(0), PERSONALITIES["sheriff"])
    assert d.players[1].max_wounds == 4 and d.players[0].max_wounds == 3
    assert d.cylinder.known()["live"] == 3 and d.cylinder.live_probability() == 0.5
    d.players[1].wounds = 3
    assert not d.game_over()
    d.players[1].wounds = 4
    assert d.game_over() and d.winner() is d.players[0]


def test_last_round_has_both_hands():
    d = new_duel(random.Random(0))
    d.play_hand(); d.play_hand()
    lr = d.last_round
    assert lr["round"] == 1 and len(lr["hands"]) == 2
    assert all(len(h["dice"]) == 5 and "points" in h for h in lr["hands"])


def test_smart_ai_locks_and_finishes_turn():
    d = make_duel(random.Random(2), PERSONALITIES["sheriff"])
    d.turn = 1
    events = take_turn(d, PERSONALITIES["sheriff"])
    assert events[-1]["type"] in ("play", "fire") and "locked" in events[-1]


def test_shoot_rival_live_only_wounds_rival():
    d = new_duel(random.Random(0))
    d.cylinder.live = 6
    d.cylinder.reload(d.rng)
    r = d.pull_trigger("rival")
    me, rival = d.players
    assert r.wounded and rival.wounds == 1 and me.wounds == 0
    assert rival.played is None  # su mano no se toca
    assert d.current is me  # sigo en mi turno


def test_shoot_rival_click_zeroes_my_hand_and_ends_turn():
    d = new_duel(random.Random(0))
    d.cylinder.live = 0
    d.cylinder.reload(d.rng)
    me, rival = d.players
    r = d.pull_trigger("rival")
    assert not r.wounded and me.played is not None and me.played.points == 0
    assert d.current is rival

