"""CLI entry point for mcp-server-doctor."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from ._version import __version__
from .doctor import apply_strict_mode, load_report, render_result, validate_report

DEFAULT_MAX_INPUT_BYTES = 10 * 1024 * 1024
_READ_CHUNK_BYTES = 64 * 1024


class InputTooLargeError(ValueError):
    """Raised when an input stream exceeds the configured byte limit."""

    def __init__(self, max_input_bytes: int) -> None:
        super().__init__(f"input exceeds --max-input-bytes limit of {max_input_bytes} bytes")


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _read_limited(stream: Any, max_input_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        read_size = min(_READ_CHUNK_BYTES, max_input_bytes - total + 1)
        chunk = stream.read(read_size)
        if not chunk:
            break
        if isinstance(chunk, str):
            encoded = chunk.encode("utf-8")
        elif isinstance(chunk, (bytes, bytearray, memoryview)):
            encoded = bytes(chunk)
        else:
            raise TypeError("input stream must return bytes or text")
        total += len(encoded)
        if total > max_input_bytes:
            raise InputTooLargeError(max_input_bytes)
        chunks.append(encoded)
    return b"".join(chunks)


def _read_input(path: str | None, max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES) -> str:
    if isinstance(max_input_bytes, bool) or not isinstance(max_input_bytes, int) or max_input_bytes <= 0:
        raise ValueError("--max-input-bytes must be a positive integer")

    if not path or path == "-":
        stream = getattr(sys.stdin, "buffer", sys.stdin)
        data = _read_limited(stream, max_input_bytes)
    else:
        with open(path, "rb") as handle:
            if os.fstat(handle.fileno()).st_size > max_input_bytes:
                raise InputTooLargeError(max_input_bytes)
            data = _read_limited(handle, max_input_bytes)
    return data.decode("utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a JSON MCP capabilities report.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("path", nargs="?", help="Report JSON path. Reads stdin when omitted or '-'.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as validation failures.")
    parser.add_argument(
        "--max-input-bytes",
        default=DEFAULT_MAX_INPUT_BYTES,
        metavar="BYTES",
        type=_positive_int,
        help=f"Maximum UTF-8 input size for files and stdin (default: {DEFAULT_MAX_INPUT_BYTES}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = load_report(_read_input(args.path, args.max_input_bytes))
    except InputTooLargeError as exc:
        print(f"mcp-server-doctor: {exc}", file=sys.stderr)
        return 2
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
