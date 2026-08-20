"""Parser for a practical subset of SQL Server CREATE TABLE DDL."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_DDL_LENGTH = 1_000_000

_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?P<name>(?:\[[^\]]+\]|[A-Za-z_][\w]*)"
    r"(?:\s*\.\s*(?:\[[^\]]+\]|[A-Za-z_][\w]*)){0,2})\s*\(",
    re.IGNORECASE,
)
_COLUMN_RE = re.compile(
    r"^(?P<name>\[[^\]]+\]|\"[^\"]+\"|[A-Za-z_][\w]*)\s+"
    r"(?P<type>\[[^\]]+\]|[A-Za-z_][\w]*)"
    r"(?P<args>\s*\([^)]*\))?",
    re.IGNORECASE,
)
_TABLE_PK_RE = re.compile(r"PRIMARY\s+KEY\b[^(]*\((?P<cols>[^)]*)\)", re.IGNORECASE)
_CONSTRAINT_KEYWORDS = (
    "PRIMARY KEY",
    "FOREIGN KEY",
    "UNIQUE",
    "CHECK",
    "CONSTRAINT",
    "INDEX",
)


class DdlParseError(ValueError):
    """Raised when the supplied DDL cannot be parsed."""


@dataclass(frozen=True)
class Column:
    """A single parsed table column."""

    name: str
    sql_type: str
    is_nullable: bool = True
    is_identity: bool = False
    is_primary_key: bool = False
    max_length: int | None = None

    def with_primary_key(self) -> "Column":
        """Return a copy flagged as part of the primary key."""
        return Column(
            name=self.name,
            sql_type=self.sql_type,
            is_nullable=self.is_nullable,
            is_identity=self.is_identity,
            is_primary_key=True,
            max_length=self.max_length,
        )


@dataclass(frozen=True)
class Table:
    """A parsed table definition."""

    name: str
    columns: tuple[Column, ...] = field(default_factory=tuple)
    schema: str | None = None


def _unquote(identifier: str) -> str:
    return identifier.strip().strip("[]").strip('"').strip()


def _split_qualified_name(raw: str) -> tuple[str | None, str]:
    parts = [_unquote(p) for p in re.split(r"\s*\.\s*", raw.strip()) if p.strip()]
    if not parts:
        raise DdlParseError("Table name is empty")
    if len(parts) == 1:
        return None, parts[0]
    return parts[-2], parts[-1]


def _extract_body(ddl: str, open_paren_index: int) -> str:
    """Return the text inside the balanced parentheses of the column list."""
    depth = 0
    for index in range(open_paren_index, len(ddl)):
        char = ddl[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return ddl[open_paren_index + 1 : index]
    raise DdlParseError("Unbalanced parentheses in CREATE TABLE body")


def _split_definitions(body: str) -> list[str]:
    """Split the column list on commas that sit at paren depth zero."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def _is_constraint(definition: str) -> bool:
    upper = " ".join(definition.upper().split())
    return any(upper.startswith(keyword) for keyword in _CONSTRAINT_KEYWORDS)


def _parse_max_length(args: str | None) -> int | None:
    if not args:
        return None
    inner = args.strip().lstrip("(").rstrip(")").strip()
    first = inner.split(",")[0].strip().lower()
    if first == "max":
        return -1
    return int(first) if first.isdigit() else None


def _parse_column(definition: str) -> Column:
    match = _COLUMN_RE.match(definition.strip())
    if match is None:
        raise DdlParseError(f"Could not parse column definition: {definition!r}")

    upper = " ".join(definition.upper().split())
    return Column(
        name=_unquote(match.group("name")),
        sql_type=_unquote(match.group("type")),
        is_nullable="NOT NULL" not in upper,
        is_identity="IDENTITY" in upper,
        is_primary_key="PRIMARY KEY" in upper,
        max_length=_parse_max_length(match.group("args")),
    )


def _apply_table_primary_keys(
    columns: tuple[Column, ...], constraints: list[str]
) -> tuple[Column, ...]:
    key_names: set[str] = set()
    for constraint in constraints:
        match = _TABLE_PK_RE.search(constraint)
        if match is None:
            continue
        for raw in match.group("cols").split(","):
            cleaned = _unquote(re.sub(r"\b(ASC|DESC)\b", "", raw, flags=re.IGNORECASE))
            if cleaned:
                key_names.add(cleaned.lower())

    if not key_names:
        return columns
    return tuple(
        column.with_primary_key() if column.name.lower() in key_names else column
        for column in columns
    )


def parse_create_table(ddl: str) -> Table:
    """Parse the first CREATE TABLE statement found in `ddl`."""
    if not isinstance(ddl, str):
        raise TypeError("ddl must be a string")
    if not ddl.strip():
        raise DdlParseError("DDL input is empty")
    if len(ddl) > MAX_DDL_LENGTH:
        raise DdlParseError(f"DDL exceeds {MAX_DDL_LENGTH} characters")

    match = _CREATE_TABLE_RE.search(ddl)
    if match is None:
        raise DdlParseError("No CREATE TABLE statement found")

    schema, name = _split_qualified_name(match.group("name"))
    body = _extract_body(ddl, match.end() - 1)

    columns: list[Column] = []
    constraints: list[str] = []
    for definition in _split_definitions(body):
        if _is_constraint(definition):
            constraints.append(definition)
        else:
            columns.append(_parse_column(definition))

    if not columns:
        raise DdlParseError(f"Table {name!r} declares no columns")

    return Table(
        name=name,
        columns=_apply_table_primary_keys(tuple(columns), constraints),
        schema=schema,
    )
