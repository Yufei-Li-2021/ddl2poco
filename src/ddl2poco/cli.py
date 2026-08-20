"""Command line interface for ddl2poco."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .emitter import emit_class
from .parser import DdlParseError, parse_create_table

EXIT_OK = 0
EXIT_ERROR = 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ddl2poco",
        description="Convert SQL Server CREATE TABLE DDL into a C# POCO class.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a .sql file. Reads stdin when omitted.",
    )
    parser.add_argument(
        "-n",
        "--namespace",
        help="Wrap the class in this file-scoped namespace.",
    )
    parser.add_argument(
        "-a",
        "--annotations",
        action="store_true",
        help="Emit EF Core data annotations ([Key], [Required], [StringLength], ...).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write to this file instead of stdout.",
    )
    return parser


def _read_source(input_path: str | None) -> str:
    if input_path is None:
        return sys.stdin.read()

    path = Path(input_path)
    if not path.is_file():
        raise DdlParseError(f"Input file not found: {input_path}")
    return path.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns a process exit code."""
    args = _build_parser().parse_args(argv)

    try:
        source = _read_source(args.input)
        table = parse_create_table(source)
        rendered = emit_class(
            table, namespace=args.namespace, annotations=args.annotations
        )
    except (DdlParseError, ValueError) as error:
        print(f"ddl2poco: {error}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as error:
        print(f"ddl2poco: could not read input: {error}", file=sys.stderr)
        return EXIT_ERROR

    if args.output:
        try:
            Path(args.output).write_text(rendered, encoding="utf-8")
        except OSError as error:
            print(f"ddl2poco: could not write output: {error}", file=sys.stderr)
            return EXIT_ERROR
    else:
        sys.stdout.write(rendered)

    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
