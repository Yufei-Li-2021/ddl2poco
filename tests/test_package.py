import ddl2poco


def test_exposes_a_version_string():
    assert isinstance(ddl2poco.__version__, str)
    assert ddl2poco.__version__.count(".") == 2
