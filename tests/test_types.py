import pytest

from ddl2poco.types import UnknownSqlTypeError, is_known_sql_type, to_csharp_type


def test_maps_int_to_csharp_int():
    result = to_csharp_type("int", is_nullable=False)
    assert result == "int"


def test_appends_question_mark_to_nullable_value_type():
    result = to_csharp_type("int", is_nullable=True)
    assert result == "int?"


def test_appends_question_mark_to_nullable_reference_type():
    result = to_csharp_type("nvarchar", is_nullable=True)
    assert result == "string?"


@pytest.mark.parametrize(
    ("sql_type", "expected"),
    [
        ("bigint", "long"),
        ("bit", "bool"),
        ("decimal", "decimal"),
        ("uniqueidentifier", "Guid"),
        ("datetime2", "DateTime"),
        ("datetimeoffset", "DateTimeOffset"),
        ("varbinary", "byte[]"),
        ("nvarchar", "string"),
    ],
)
def test_maps_common_sql_server_types(sql_type, expected):
    assert to_csharp_type(sql_type, is_nullable=False) == expected


def test_ignores_brackets_and_casing_around_type_name():
    assert to_csharp_type("[INT]", is_nullable=False) == "int"


def test_falls_back_to_object_for_unknown_type():
    assert to_csharp_type("geography", is_nullable=False) == "object"


def test_raises_for_unknown_type_when_strict():
    with pytest.raises(UnknownSqlTypeError):
        to_csharp_type("geography", is_nullable=False, strict=True)


def test_raises_when_sql_type_is_blank():
    with pytest.raises(ValueError):
        to_csharp_type("   ", is_nullable=False)


def test_reports_whether_type_is_known():
    assert is_known_sql_type("nvarchar") is True
    assert is_known_sql_type("geography") is False
