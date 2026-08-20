import pytest

from ddl2poco.emitter import emit_class, to_pascal_case, to_property_name
from ddl2poco.parser import parse_create_table

DDL = """
CREATE TABLE [dbo].[Employee] (
    [EmployeeId] INT IDENTITY(1,1) NOT NULL,
    [FirstName] NVARCHAR(100) NOT NULL,
    [MiddleName] NVARCHAR(100) NULL
);
"""


def test_emits_class_named_after_table():
    rendered = emit_class(parse_create_table(DDL))

    assert "public class Employee" in rendered


def test_emits_one_property_per_column():
    rendered = emit_class(parse_create_table(DDL))

    assert "public int EmployeeId { get; set; }" in rendered
    assert "public string FirstName { get; set; }" in rendered
    assert "public string? MiddleName { get; set; }" in rendered


def test_omits_namespace_when_not_requested():
    rendered = emit_class(parse_create_table(DDL))

    assert "namespace" not in rendered


def test_wraps_class_in_file_scoped_namespace_when_requested():
    rendered = emit_class(parse_create_table(DDL), namespace="Hr.Domain")

    assert rendered.startswith("namespace Hr.Domain;\n")


def test_converts_snake_case_table_to_pascal_case():
    rendered = emit_class(parse_create_table("CREATE TABLE pay_run (id INT NOT NULL)"))

    assert "public class PayRun" in rendered


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("employee_id", "EmployeeId"),
        ("EmployeeId", "EmployeeId"),
        ("pay-run", "PayRun"),
        ("first name", "FirstName"),
    ],
)
def test_pascal_case_conversion(identifier, expected):
    assert to_pascal_case(identifier) == expected


def test_pascal_case_raises_on_blank_identifier():
    with pytest.raises(ValueError):
        to_pascal_case("   ")


def test_escapes_property_named_after_csharp_keyword():
    assert to_property_name("class", "Widget") == "@Class"


def test_suffixes_property_that_collides_with_class_name():
    assert to_property_name("Employee", "Employee") == "EmployeeValue"


def test_prefixes_property_starting_with_a_digit():
    assert to_property_name("1st_line", "Address") == "_1stLine"


def test_rendered_output_ends_with_newline():
    rendered = emit_class(parse_create_table(DDL))

    assert rendered.endswith("}\n")
