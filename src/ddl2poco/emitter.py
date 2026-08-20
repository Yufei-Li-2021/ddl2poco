"""Render parsed tables as C# POCO classes."""

from __future__ import annotations

import re
from collections.abc import Sequence

from .parser import Table
from .types import csharp_base_type, is_value_type, to_csharp_type

INDENT = "    "

VALIDATION_USING = "using System.ComponentModel.DataAnnotations;"
SCHEMA_USING = "using System.ComponentModel.DataAnnotations.Schema;"

#: NVARCHAR(MAX) and friends parse to this sentinel and carry no usable length.
_UNBOUNDED_LENGTH = -1

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


def _annotations_for(column, property_name: str) -> tuple[str, ...]:
    """Return the data annotation lines that apply to `column`."""
    annotations: list[str] = []

    if column.is_primary_key:
        annotations.append("[Key]")
    if column.is_identity:
        annotations.append("[DatabaseGenerated(DatabaseGeneratedOption.Identity)]")
    if property_name.lstrip("@") != column.name:
        annotations.append(f'[Column("{column.name}")]')
    if not column.is_nullable and not is_value_type(column.sql_type):
        annotations.append("[Required]")

    is_string = csharp_base_type(column.sql_type) == "string"
    has_bound_length = (
        column.max_length is not None and column.max_length > _UNBOUNDED_LENGTH
    )
    if is_string and has_bound_length:
        annotations.append(f"[StringLength({column.max_length})]")

    return tuple(annotations)


def _required_usings(annotation_lines: list[str]) -> list[str]:
    """Return the using directives the emitted annotations depend on."""
    joined = "".join(annotation_lines)
    usings: list[str] = []
    if any(tag in joined for tag in ("[Key]", "[Required]", "[StringLength")):
        usings.append(VALIDATION_USING)
    if any(tag in joined for tag in ("[DatabaseGenerated", "[Column(")):
        usings.append(SCHEMA_USING)
    return usings


def _property_line(csharp_type: str, property_name: str) -> str:
    return f"{INDENT}public {csharp_type} {property_name} {{ get; set; }}"


def _render_class(table: Table, annotations: bool) -> tuple[list[str], list[str]]:
    """Return the rendered lines for one class and the annotations it used."""
    class_name = to_pascal_case(table.name)
    body: list[str] = []
    used: list[str] = []

    for index, column in enumerate(table.columns):
        property_name = to_property_name(column.name, class_name)
        if annotations:
            column_annotations = _annotations_for(column, property_name)
            used.extend(column_annotations)
            if column_annotations and index > 0:
                body.append("")
            body.extend(f"{INDENT}{line}" for line in column_annotations)
        csharp_type = to_csharp_type(column.sql_type, is_nullable=column.is_nullable)
        body.append(_property_line(csharp_type, property_name))

    return [f"public class {class_name}", "{", *body, "}"], used


def emit_classes(
    tables: Sequence[Table], *, namespace: str | None = None, annotations: bool = False
) -> str:
    """Render every table in `tables` into a single C# source file.

    Using directives and the namespace declaration are emitted once, ahead of
    all classes.
    """
    if not tables:
        raise ValueError("tables must not be empty")

    rendered: list[list[str]] = []
    used: list[str] = []
    for table in tables:
        if table is None:
            raise ValueError("tables must not contain None")
        class_lines, class_annotations = _render_class(table, annotations)
        rendered.append(class_lines)
        used.extend(class_annotations)

    lines: list[str] = []
    usings = _required_usings(used) if annotations else []
    if usings:
        lines.extend(usings)
        lines.append("")
    if namespace:
        lines.append(f"namespace {namespace};")
        lines.append("")

    for index, class_lines in enumerate(rendered):
        if index > 0:
            lines.append("")
        lines.extend(class_lines)

    return "\n".join(lines) + "\n"


def emit_class(
    table: Table, *, namespace: str | None = None, annotations: bool = False
) -> str:
    """Render a single table as a C# class."""
    if table is None:
        raise ValueError("table must not be None")
    return emit_classes((table,), namespace=namespace, annotations=annotations)
