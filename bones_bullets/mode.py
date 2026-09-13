"""Contrato de una mesa. Campaña y duelo lo implementarán después.

No cambia reglas: el kernel sigue en dice/hands/revolver/results.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .results import HandResult, TriggerResult


class Match(ABC):
    """Una partida: alguien actúa, hay tambor, la partida puede terminar."""

    @abstractmethod
    def game_over(self) -> bool:
        """True si ya no se aceptan acciones de juego."""

    @abstractmethod
    def toggle_lock(self, index: int) -> bool:
        """Bloquea o libera un dado de quien tiene el turno."""

    @abstractmethod
    def pull_trigger(self, target: str = "self") -> TriggerResult:
        """Aprieta el gatillo. target es 'self' o 'rival'."""

    @abstractmethod
    def play_hand(self) -> HandResult:
        """Cierra la mano de quien tiene el turno."""
