import pytest

from ddl2poco.parser import DdlParseError, parse_create_table

SIMPLE_DDL = """
CREATE TABLE [dbo].[Employee] (
    [EmployeeId] INT IDENTITY(1,1) NOT NULL,
    [FirstName] NVARCHAR(100) NOT NULL,
    [MiddleName] NVARCHAR(100) NULL,
    [HireDate] DATE NOT NULL,
    CONSTRAINT [PK_Employee] PRIMARY KEY CLUSTERED ([EmployeeId] ASC)
);
"""


def test_parses_table_and_schema_name():
    table = parse_create_table(SIMPLE_DDL)

    assert table.name == "Employee"
    assert table.schema == "dbo"


def test_parses_every_column():
    table = parse_create_table(SIMPLE_DDL)

    names = [column.name for column in table.columns]
    assert names == ["EmployeeId", "FirstName", "MiddleName", "HireDate"]


def test_marks_not_null_columns_as_non_nullable():
    table = parse_create_table(SIMPLE_DDL)

    by_name = {column.name: column for column in table.columns}
    assert by_name["FirstName"].is_nullable is False
    assert by_name["MiddleName"].is_nullable is True


def test_detects_identity_columns():
    table = parse_create_table(SIMPLE_DDL)

    assert table.columns[0].is_identity is True
    assert table.columns[1].is_identity is False


def test_applies_table_level_primary_key_to_column():
    table = parse_create_table(SIMPLE_DDL)

    by_name = {column.name: column for column in table.columns}
    assert by_name["EmployeeId"].is_primary_key is True
    assert by_name["FirstName"].is_primary_key is False


def test_detects_inline_primary_key():
    ddl = "CREATE TABLE Widget (Id INT NOT NULL PRIMARY KEY, Name VARCHAR(50) NULL)"

    table = parse_create_table(ddl)

    assert table.columns[0].is_primary_key is True


def test_captures_declared_max_length():
    table = parse_create_table(SIMPLE_DDL)

    assert table.columns[1].max_length == 100


def test_represents_varchar_max_as_negative_one():
    ddl = "CREATE TABLE Doc (Body NVARCHAR(MAX) NULL)"

    table = parse_create_table(ddl)

    assert table.columns[0].max_length == -1


def test_ignores_decimal_precision_as_max_length():
    ddl = "CREATE TABLE Pay (Amount DECIMAL(18, 2) NOT NULL)"

    table = parse_create_table(ddl)

    assert table.columns[0].max_length == 18


def test_parses_unqualified_table_name_without_schema():
    table = parse_create_table("CREATE TABLE Widget (Id INT NOT NULL)")

    assert table.name == "Widget"
    assert table.schema is None


def test_skips_foreign_key_and_check_constraints():
    ddl = """
    CREATE TABLE [Order] (
        Id INT NOT NULL,
        CustomerId INT NOT NULL,
        CONSTRAINT FK_Order_Customer FOREIGN KEY (CustomerId) REFERENCES Customer(Id),
        CHECK (Id > 0)
    )
    """

    table = parse_create_table(ddl)

    assert [column.name for column in table.columns] == ["Id", "CustomerId"]


def test_raises_when_no_create_table_present():
    with pytest.raises(DdlParseError):
        parse_create_table("SELECT 1")


def test_raises_when_input_is_empty():
    with pytest.raises(DdlParseError):
        parse_create_table("   ")


def test_raises_when_parentheses_are_unbalanced():
    with pytest.raises(DdlParseError):
        parse_create_table("CREATE TABLE Widget (Id INT NOT NULL")


def test_raises_when_input_is_not_a_string():
    with pytest.raises(TypeError):
        parse_create_table(None)
