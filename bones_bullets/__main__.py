import sys

from .cli import run

if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(run(seed))
