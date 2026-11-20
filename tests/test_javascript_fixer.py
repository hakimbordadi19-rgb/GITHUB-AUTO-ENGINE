from engine.javascript_fixer import (
    inspect_javascript,
    repair_javascript,
)


def test_missing_file():
    result = repair_javascript("missing_file.js")
    assert result["status"] == "NOT_FOUND"


def test_already_valid(tmp_path):
    file = tmp_path / "valid.js"
    file.write_text('console.log("Hello");\n')

    result = repair_javascript(file)
    assert result["status"] == "ALREADY_VALID"


def test_repair_missing_parenthesis(tmp_path):
    file = tmp_path / "broken.js"
    file.write_text('console.log("Hello"\n')

    result = repair_javascript(file)

    assert result["status"] == "REPAIRED"
    assert result["validation"] == "OK"
    assert inspect_javascript(file)["status"] == "OK"


def test_unsupported_error(tmp_path):
    file = tmp_path / "broken.js"
    file.write_text('const = ;\n')

    result = repair_javascript(file)
    assert result["status"] == "UNSUPPORTED_ERROR"


def test_backup_created(tmp_path):
    file = tmp_path / "backup.js"
    file.write_text('console.log("Backup"\n')

    result = repair_javascript(file)

    assert result["status"] == "REPAIRED"
    assert result["backup"]
