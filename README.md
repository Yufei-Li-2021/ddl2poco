# ddl2poco

Convert SQL Server `CREATE TABLE` DDL into C# POCO / EF Core entity classes.

Paste the DDL you already have — straight out of SSMS, a migration script, or a
`.sql` file in the repo — and get a matching C# class back. No database
connection, no scaffolding context, no dependencies.

```console
$ ddl2poco schema/EmployeePayRun.sql --namespace HrWize.Payroll.Domain
```

```csharp
namespace HrWize.Payroll.Domain;

public class EmployeePayRun
{
    public long PayRunId { get; set; }
    public int EmployeeId { get; set; }
    public decimal GrossAmount { get; set; }
    public string Currency { get; set; }
    public DateTimeOffset? ProcessedOn { get; set; }
    public string? Notes { get; set; }
    public bool IsFinalised { get; set; }
    public byte[] RowVersion { get; set; }
}
```

## Why

`dotnet ef dbcontext scaffold` needs a live database and generates an entire
context. Often you just have a DDL snippet — a table someone pasted into a
ticket, a script from a vendor, a proposed migration that does not exist yet —
and you want the entity class for it. That is all this does.

## Install

```console
pip install ddl2poco
```

Or run it straight from a clone:

```console
python -m ddl2poco.cli schema.sql
```

## Usage

```console
ddl2poco [input.sql] [-n NAMESPACE] [-a] [-o OUTPUT.cs]
```

| Flag | Effect |
| --- | --- |
| `input.sql` | Path to the DDL file. Reads **stdin** when omitted. |
| `-n`, `--namespace` | Wrap the class in a file-scoped namespace. |
| `-a`, `--annotations` | Emit EF Core data annotations. |
| `-o`, `--output` | Write to a file instead of stdout. |

Piping works, so it composes with whatever you already use:

```console
$ pbpaste | ddl2poco -n Hr.Domain -o Employee.cs
```

### EF Core data annotations

Pass `--annotations` to derive attributes from the DDL you already parsed:

```csharp
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

public class EmployeePayRun
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public long PayRunId { get; set; }

    [Required]
    [StringLength(3)]
    public string Currency { get; set; }
}
```

| Attribute | Derived from |
| --- | --- |
| `[Key]` | Inline or table-level `PRIMARY KEY` |
| `[DatabaseGenerated(...Identity)]` | `IDENTITY(1,1)` |
| `[Required]` | `NOT NULL` on a reference-typed column |
| `[StringLength(n)]` | Declared length on a string column, skipping `MAX` |
| `[Column("...")]` | Property name differing from the SQL column name |

Using directives are emitted only when the attributes actually need them.

## What it handles

- Bracketed, quoted, and bare identifiers (`[dbo].[Employee]`, `Employee`)
- `NOT NULL` / `NULL` → nullable value types and nullable reference types
- `IDENTITY(1,1)` detection
- Inline and table-level `PRIMARY KEY`, including `CLUSTERED (col ASC)`
- `FOREIGN KEY`, `UNIQUE`, and `CHECK` constraints skipped cleanly
- `NVARCHAR(MAX)` and precision arguments like `DECIMAL(18, 2)`
- `snake_case` and `kebab-case` names converted to PascalCase
- C# keyword collisions escaped (`class` → `@Class`)
- Properties that would collide with the class name (`Employee.Employee` → `EmployeeValue`)

### Type mapping

| SQL Server | C# |
| --- | --- |
| `bigint` / `int` / `smallint` / `tinyint` | `long` / `int` / `short` / `byte` |
| `bit` | `bool` |
| `decimal` / `numeric` / `money` / `smallmoney` | `decimal` |
| `float` / `real` | `double` / `float` |
| `char` / `varchar` / `nchar` / `nvarchar` / `text` / `xml` | `string` |
| `date` / `time` | `DateOnly` / `TimeOnly` |
| `datetime` / `datetime2` / `smalldatetime` | `DateTime` |
| `datetimeoffset` | `DateTimeOffset` |
| `uniqueidentifier` | `Guid` |
| `binary` / `varbinary` / `image` / `rowversion` | `byte[]` |

Unrecognised types fall back to `object` rather than failing the run.

## Limitations

It is a focused parser, not a full T-SQL grammar. It reads the **first**
`CREATE TABLE` in the input and does not resolve foreign keys into navigation
properties, expand user-defined types, or read computed column expressions.

## Development

```console
python -m venv .venv && .venv/Scripts/activate
pip install -e ".[dev]"
pytest --cov=ddl2poco --cov-report=term-missing
```

## License

MIT
