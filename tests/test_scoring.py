from bones_bullets.scoring import apply_streak_and_silver


def test_sin_racha_ni_plata():
    mult, points = apply_streak_and_silver(10, 2.0, 0, False, 0.5, 3.0)
    assert mult == 2.0
    assert points == 20


def test_racha_suma_al_mult():
    mult, points = apply_streak_and_silver(10, 2.0, 2, False, 0.5, 3.0)
    assert mult == 3.0
    assert points == 30


def test_plata_multiplica_despues_de_la_racha():
    mult, points = apply_streak_and_silver(10, 2.0, 2, True, 0.5, 3.0)
    assert mult == 9.0
    assert points == 90
