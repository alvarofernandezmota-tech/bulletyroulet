"""python -m bones_bullets [semilla] [rival]        duelo contra la IA
"""
import sys

from .ai import DEFAULT_RIVAL, PERSONALITIES
from .cli_duel import run_duel


def main(argv: list[str]) -> int:
    rival = next((a for a in argv if a in PERSONALITIES), DEFAULT_RIVAL)
    nums = [a for a in argv if a.lstrip("-").isdigit()]
    return run_duel(int(nums[0]) if nums else None, rival)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
