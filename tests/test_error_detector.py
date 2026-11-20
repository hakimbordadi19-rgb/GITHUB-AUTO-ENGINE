from engine.error_detector import inspect_file


def test_valid_python(tmp_path):
    source = tmp_path / "valid.py"
    source.write_text('print("HELLO")\n')

    result = inspect_file(str(source), "Python")

    assert result["status"] == "OK"
    assert result["errors"] == []


def test_invalid_python(tmp_path):
    source = tmp_path / "broken.py"
    source.write_text('print("BROKEN"\n')

    result = inspect_file(str(source), "Python")

    assert result["status"] == "ERROR"
    assert result["errors"]


def test_unsupported_language(tmp_path):
    source = tmp_path / "test.txt"
    source.write_text("hello")

    result = inspect_file(str(source), "Unknown")

    assert result["status"] == "ERROR"
    assert result["errors"]


def test_valid_php(tmp_path):
    source = tmp_path / "valid.php"
    source.write_text('<?php\necho "HELLO";\n')

    result = inspect_file(str(source), "PHP")

    assert result["status"] == "OK"
    assert result["errors"] == []


def test_invalid_php(tmp_path):
    source = tmp_path / "broken.php"
    source.write_text('<?php\necho "BROKEN"\n')

    result = inspect_file(str(source), "PHP")

    assert result["status"] == "ERROR"
    assert result["errors"]
