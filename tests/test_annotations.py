import pytest

from ddl2poco.emitter import emit_class
from ddl2poco.parser import parse_create_table

DDL = """
CREATE TABLE [dbo].[EmployeePayRun] (
    [PayRunId]    BIGINT         IDENTITY(1,1) NOT NULL,
    [Currency]    NCHAR(3)       NOT NULL,
    [Notes]       NVARCHAR(MAX)  NULL,
    [GrossAmount] DECIMAL(18, 2) NOT NULL,
    CONSTRAINT [PK_EmployeePayRun] PRIMARY KEY CLUSTERED ([PayRunId] ASC)
);
"""


@pytest.fixture()
def rendered():
    return emit_class(parse_create_table(DDL), annotations=True)


def test_marks_primary_key_with_key_attribute(rendered):
    assert "[Key]" in rendered


def test_marks_identity_column_as_database_generated(rendered):
    assert "[DatabaseGenerated(DatabaseGeneratedOption.Identity)]" in rendered


def test_marks_not_null_string_column_as_required(rendered):
    assert "[Required]" in rendered


def test_applies_string_length_from_declared_length(rendered):
    assert "[StringLength(3)]" in rendered


def test_omits_string_length_for_unbounded_nvarchar_max(rendered):
    assert "[StringLength(-1)]" not in rendered


def test_does_not_mark_value_types_as_required():
    ddl = "CREATE TABLE T (Amount DECIMAL(18,2) NOT NULL)"

    result = emit_class(parse_create_table(ddl), annotations=True)

    assert "[Required]" not in result


def test_does_not_apply_string_length_to_numeric_precision(rendered):
    assert "[StringLength(18)]" not in rendered


def test_emits_column_attribute_when_property_name_differs():
    ddl = "CREATE TABLE T (employee_id INT NOT NULL)"

    result = emit_class(parse_create_table(ddl), annotations=True)

    assert '[Column("employee_id")]' in result


def test_omits_column_attribute_when_names_match(rendered):
    assert '[Column("PayRunId")]' not in rendered


def test_includes_validation_using_directive(rendered):
    assert rendered.startswith("using System.ComponentModel.DataAnnotations;")


def test_includes_schema_using_directive(rendered):
    assert "using System.ComponentModel.DataAnnotations.Schema;" in rendered


def test_omits_schema_using_when_no_schema_attributes_apply():
    ddl = "CREATE TABLE T (Name NVARCHAR(50) NOT NULL)"

    result = emit_class(parse_create_table(ddl), annotations=True)

    assert "DataAnnotations.Schema" not in result


def test_output_is_unchanged_when_annotations_disabled():
    table = parse_create_table(DDL)

    assert emit_class(table) == emit_class(table, annotations=False)


def test_usings_precede_namespace_declaration():
    result = emit_class(parse_create_table(DDL), namespace="Hr.Domain", annotations=True)

    assert result.index("using System") < result.index("namespace Hr.Domain;")
