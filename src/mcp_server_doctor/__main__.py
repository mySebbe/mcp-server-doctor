"""CLI entry point for mcp-server-doctor."""

from __future__ import annotations

import argparse
import sys

from ._version import __version__
from .doctor import apply_strict_mode, load_report, render_result, validate_report


def _read_input(path: str | None) -> str:
    if not path or path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a JSON MCP capabilities report.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("path", nargs="?", help="Report JSON path. Reads stdin when omitted or '-'.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as validation failures.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = load_report(_read_input(args.path))
    except OSError as exc:
        print(f"mcp-server-doctor: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"mcp-server-doctor: invalid JSON: {exc}", file=sys.stderr)
        return 2

    result = apply_strict_mode(validate_report(report), args.strict)
    sys.stdout.write(render_result(result, args.format))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
