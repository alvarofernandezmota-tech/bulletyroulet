"""python -m bones_bullets [semilla]            modo solitario
python -m bones_bullets --duelo [rival] [semilla]   duelo contra la máquina (cauto | tahur | loco)
"""
import sys

from .cli import run


def main(argv: list[str]) -> int:
    args = [a for a in argv if a not in ("--duelo", "--duel")]
    if len(args) != len(argv):
        from .ai import PERSONALITIES
        from .cli_duel import run_duel
        rival = next((a for a in args if a in PERSONALITIES), "tahur")
        nums = [a for a in args if a.lstrip("-").isdigit()]
        return run_duel(int(nums[0]) if nums else None, rival)
    seed = int(args[0]) if args and args[0].lstrip("-").isdigit() else None
    return run(seed)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
