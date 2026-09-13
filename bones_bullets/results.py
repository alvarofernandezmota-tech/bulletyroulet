"""Tipos de resultado compartidos entre campaña y duelo."""
from __future__ import annotations

from dataclasses import dataclass

from .hands import HandType
from .revolver import Chamber


@dataclass
class HandResult:
    hand: HandType
    total: int
    mult: float
    points: int


@dataclass
class TriggerResult:
    chamber: Chamber
    wounded: bool = False
    shielded: bool = False
