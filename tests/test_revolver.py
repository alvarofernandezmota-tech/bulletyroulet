import random

from bones_bullets.revolver import Chamber, Cylinder


def test_reload_contents():
    c = Cylinder(size=6, live=1, blanks=1, silver=1)
    c.reload(random.Random(0))
    assert len(c.chambers) == 6
    assert c.chambers.count(Chamber.LIVE) == 1
    assert c.chambers.count(Chamber.BLANK) == 1
    assert c.chambers.count(Chamber.SILVER) == 1
    assert c.chambers.count(Chamber.EMPTY) == 3
    assert c.known() == {"remaining": 6, "live": 1, "blank": 1, "silver": 1}


def test_risk_rises_each_click():
    rng = random.Random(1)
    c = Cylinder()
    c.reload(rng)
    risk = c.live_probability()
    assert risk == 1 / 6
    for _ in range(5):
        res = c.pull_trigger(rng)
        if res is Chamber.LIVE:
            assert c.known()["remaining"] == 6  # recargado
            return
        assert c.live_probability() > risk
        risk = c.live_probability()


def test_bang_inevitable_within_six_pulls():
    for seed in range(50):
        rng = random.Random(seed)
        c = Cylinder()
        c.reload(rng)
        results = [c.pull_trigger(rng) for _ in range(6)]
        assert Chamber.LIVE in results


def test_reload_after_bang_and_when_empty():
    rng = random.Random(3)
    c = Cylinder(size=6, live=0)
    c.reload(rng)
    for _ in range(5):
        c.pull_trigger(rng)
    assert c.known()["remaining"] == 1
    c.pull_trigger(rng)
    assert c.known()["remaining"] == 6
