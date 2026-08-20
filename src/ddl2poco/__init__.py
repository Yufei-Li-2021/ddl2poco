"""Convert SQL Server CREATE TABLE DDL into C# POCO classes."""

from .emitter import emit_class
from .parser import Column, DdlParseError, Table, parse_create_table
from .types import UnknownSqlTypeError, to_csharp_type

__version__ = "0.1.0"

__all__ = [
    "Column",
    "DdlParseError",
    "Table",
    "UnknownSqlTypeError",
    "emit_class",
    "parse_create_table",
    "to_csharp_type",
]
