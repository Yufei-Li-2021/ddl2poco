import pytest

from ddl2poco.emitter import emit_classes
from ddl2poco.parser import DdlParseError, parse_all_tables, parse_create_table

TWO_TABLES = """
CREATE TABLE [dbo].[Employee] (
    [EmployeeId] INT IDENTITY(1,1) NOT NULL,
    [FirstName]  NVARCHAR(100) NOT NULL,
    CONSTRAINT [PK_Employee] PRIMARY KEY CLUSTERED ([EmployeeId] ASC)
);

CREATE TABLE [dbo].[Department] (
    [DepartmentId] INT NOT NULL PRIMARY KEY,
    [Name]         NVARCHAR(50) NULL
);
"""


def test_parses_every_table_in_the_script():
    tables = parse_all_tables(TWO_TABLES)

    assert [table.name for table in tables] == ["Employee", "Department"]


def test_preserves_source_order():
    tables = parse_all_tables(TWO_TABLES)

    assert tables[0].name == "Employee"


def test_parses_columns_of_the_second_table():
    tables = parse_all_tables(TWO_TABLES)

    assert [column.name for column in tables[1].columns] == ["DepartmentId", "Name"]


def test_single_table_script_returns_one_table():
    tables = parse_all_tables("CREATE TABLE Widget (Id INT NOT NULL)")

    assert len(tables) == 1


def test_parse_create_table_still_returns_the_first_table():
    assert parse_create_table(TWO_TABLES).name == "Employee"


def test_raises_when_no_table_present():
    with pytest.raises(DdlParseError):
        parse_all_tables("SELECT 1")


def test_emits_a_class_for_every_table():
    rendered = emit_classes(parse_all_tables(TWO_TABLES))

    assert "public class Employee" in rendered
    assert "public class Department" in rendered


def test_separates_classes_with_a_blank_line():
    rendered = emit_classes(parse_all_tables(TWO_TABLES))

    assert "}\n\npublic class Department" in rendered


def test_emits_namespace_only_once():
    rendered = emit_classes(parse_all_tables(TWO_TABLES), namespace="Hr.Domain")

    assert rendered.count("namespace Hr.Domain;") == 1


def test_emits_each_using_directive_only_once():
    rendered = emit_classes(parse_all_tables(TWO_TABLES), annotations=True)

    assert rendered.count("using System.ComponentModel.DataAnnotations;") == 1


def test_annotations_apply_across_all_classes():
    rendered = emit_classes(parse_all_tables(TWO_TABLES), annotations=True)

    assert rendered.count("[Key]") == 2


def test_raises_when_table_sequence_is_empty():
    with pytest.raises(ValueError):
        emit_classes([])


def test_raises_when_table_sequence_contains_none():
    with pytest.raises(ValueError):
        emit_classes([None])
