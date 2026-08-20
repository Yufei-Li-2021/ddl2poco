"""SQL Server -> C# type mapping."""

from __future__ import annotations

from types import MappingProxyType

#: SQL Server base type name -> (C# type, is_value_type)
_TYPE_MAP: MappingProxyType = MappingProxyType(
    {
        "bigint": ("long", True),
        "int": ("int", True),
        "smallint": ("short", True),
        "tinyint": ("byte", True),
        "bit": ("bool", True),
        "decimal": ("decimal", True),
        "numeric": ("decimal", True),
        "money": ("decimal", True),
        "smallmoney": ("decimal", True),
        "float": ("double", True),
        "real": ("float", True),
        "date": ("DateOnly", True),
        "datetime": ("DateTime", True),
        "datetime2": ("DateTime", True),
        "smalldatetime": ("DateTime", True),
        "datetimeoffset": ("DateTimeOffset", True),
        "time": ("TimeOnly", True),
        "uniqueidentifier": ("Guid", True),
        "char": ("string", False),
        "varchar": ("string", False),
        "nchar": ("string", False),
        "nvarchar": ("string", False),
        "text": ("string", False),
        "ntext": ("string", False),
        "xml": ("string", False),
        "sysname": ("string", False),
        "binary": ("byte[]", False),
        "varbinary": ("byte[]", False),
        "image": ("byte[]", False),
        "rowversion": ("byte[]", False),
        "timestamp": ("byte[]", False),
    }
)

UNKNOWN_CSHARP_TYPE = "object"


class UnknownSqlTypeError(ValueError):
    """Raised when a SQL Server type has no known C# equivalent."""


def to_csharp_type(sql_type: str, *, is_nullable: bool, strict: bool = False) -> str:
    """Return the C# type for a SQL Server type name.

    Value types gain a trailing '?' when nullable; reference types gain one too,
    matching C# nullable reference type conventions.
    """
    if not sql_type or not sql_type.strip():
        raise ValueError("sql_type must be a non-empty string")

    key = sql_type.strip().strip("[]").lower()
    mapped = _TYPE_MAP.get(key)

    if mapped is None:
        if strict:
            raise UnknownSqlTypeError(f"No C# mapping for SQL type {sql_type!r}")
        base = UNKNOWN_CSHARP_TYPE
    else:
        base = mapped[0]

    return f"{base}?" if is_nullable else base


def is_known_sql_type(sql_type: str) -> bool:
    """Return True when the SQL Server type has a known C# mapping."""
    return sql_type.strip().strip("[]").lower() in _TYPE_MAP
