import pytest

from ddl2poco.cli import main

DDL = "CREATE TABLE [dbo].[Widget] (Id INT NOT NULL, Name NVARCHAR(50) NULL);"


@pytest.fixture()
def ddl_file(tmp_path):
    path = tmp_path / "widget.sql"
    path.write_text(DDL, encoding="utf-8")
    return path


def test_writes_generated_class_to_stdout(ddl_file, capsys):
    exit_code = main([str(ddl_file)])

    assert exit_code == 0
    assert "public class Widget" in capsys.readouterr().out


def test_reads_ddl_from_stdin_when_no_path_given(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(DDL))

    exit_code = main([])

    assert exit_code == 0
    assert "public class Widget" in capsys.readouterr().out


def test_writes_to_output_file_when_requested(ddl_file, tmp_path):
    destination = tmp_path / "Widget.cs"

    exit_code = main([str(ddl_file), "--output", str(destination)])

    assert exit_code == 0
    assert "public class Widget" in destination.read_text(encoding="utf-8")


def test_applies_requested_namespace(ddl_file, capsys):
    main([str(ddl_file), "--namespace", "Hr.Domain"])

    assert "namespace Hr.Domain;" in capsys.readouterr().out


def test_returns_error_code_for_missing_input_file(tmp_path, capsys):
    exit_code = main([str(tmp_path / "nope.sql")])

    assert exit_code == 1
    assert "ddl2poco:" in capsys.readouterr().err


def test_returns_error_code_for_unparsable_ddl(tmp_path, capsys):
    path = tmp_path / "bad.sql"
    path.write_text("SELECT 1", encoding="utf-8")

    exit_code = main([str(path)])

    assert exit_code == 1
    assert "ddl2poco:" in capsys.readouterr().err
