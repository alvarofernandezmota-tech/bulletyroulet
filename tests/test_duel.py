import random

from bones_bullets.ai import PERSONALITIES, take_turn
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
