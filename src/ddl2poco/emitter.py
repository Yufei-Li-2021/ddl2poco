"""Render parsed tables as C# POCO classes."""

from __future__ import annotations

import keyword
import re

from .parser import Table
from .types import to_csharp_type

INDENT = "    "

_CSHARP_KEYWORDS = frozenset(
    {
        "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
        "char", "checked", "class", "const", "continue", "decimal", "default",
        "delegate", "do", "double", "else", "enum", "event", "explicit",
        "extern", "false", "finally", "fixed", "float", "for", "foreach",
        "goto", "if", "implicit", "in", "int", "interface", "internal", "is",
        "lock", "long", "namespace", "new", "null", "object", "operator",
        "out", "override", "params", "private", "protected", "public",
        "readonly", "ref", "return", "sbyte", "sealed", "short", "sizeof",
        "stackalloc", "static", "string", "struct", "switch", "this", "throw",
        "true", "try", "typeof", "uint", "ulong", "unchecked", "unsafe",
        "ushort", "using", "virtual", "void", "volatile", "while",
    }
)


def to_pascal_case(identifier: str) -> str:
    """Convert a SQL identifier to PascalCase, preserving existing casing."""
    if not identifier or not identifier.strip():
        raise ValueError("identifier must be a non-empty string")

    words = [w for w in re.split(r"[\s_\-]+", identifier.strip()) if w]
    if not words:
        raise ValueError(f"identifier {identifier!r} contains no usable characters")

    return "".join(w[:1].upper() + w[1:] for w in words)


def to_property_name(column_name: str, class_name: str) -> str:
    """Return a legal C# property name that cannot collide with its class."""
    name = to_pascal_case(column_name)
    if not name[0].isalpha() and name[0] != "_":
        name = f"_{name}"
    if name.lower() in _CSHARP_KEYWORDS:
        name = f"@{name}"
    if name == class_name:
        name = f"{name}Value"
    return name


def _property_line(csharp_type: str, property_name: str) -> str:
    return f"{INDENT}public {csharp_type} {property_name} {{ get; set; }}"


def emit_class(table: Table, *, namespace: str | None = None) -> str:
    """Render `table` as a C# class, optionally wrapped in a file-scoped namespace."""
    if table is None:
        raise ValueError("table must not be None")

    class_name = to_pascal_case(table.name)
    lines: list[str] = []

    if namespace:
        lines.append(f"namespace {namespace};")
        lines.append("")

    lines.append(f"public class {class_name}")
    lines.append("{")
    for column in table.columns:
        csharp_type = to_csharp_type(column.sql_type, is_nullable=column.is_nullable)
        lines.append(_property_line(csharp_type, to_property_name(column.name, class_name)))
    lines.append("}")

    return "\n".join(lines) + "\n"
