from bones_bullets.mode import Match
from bones_bullets.results import HandResult, TriggerResult
from bones_bullets.hands import HandType
from bones_bullets.revolver import Chamber


def test_no_se_instancia_la_clase_abstracta():
    try:
        Match()
        raise AssertionError("Match no debe instanciarse")
    except TypeError:
        pass


class Dummy(Match):
    def game_over(self) -> bool:
        return False

    def toggle_lock(self, index: int) -> bool:
        return index == 0

    def pull_trigger(self, target: str = "self") -> TriggerResult:
        return TriggerResult(next(iter(Chamber)))

    def play_hand(self) -> HandResult:
        return HandResult(HandType.HIGH_CARD, 1, 1.0, 1)


def test_subclase_cumple_el_contrato():
    m = Dummy()
    assert m.game_over() is False
    assert m.toggle_lock(0) is True
    assert isinstance(m.pull_trigger(), TriggerResult)
    assert m.play_hand().points == 1
