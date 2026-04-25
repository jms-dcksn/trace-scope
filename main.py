"""Legacy CLI entry. Prefer `python -m evals`.

Usage:
    uv run main.py              # full dataset eval
    uv run main.py 3-5-7        # only cases 3, 5, 7
    uv run main.py judge-check  # judge stability on fixed outputs
    uv run main.py judge-pr     # judge precision/recall on golden dataset
"""
import sys

from evals.__main__ import build_parser


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    parser = build_parser()
    if cmd is None:
        args = parser.parse_args(["run"])
    elif cmd in ("judge-check", "judge-pr"):
        args = parser.parse_args([cmd])
    elif all(c.isdigit() or c == "-" for c in cmd):
        args = parser.parse_args(["run", "--cases", cmd])
    else:
        args = parser.parse_args(sys.argv[1:])
    args.func(args)


if __name__ == "__main__":
    main()
