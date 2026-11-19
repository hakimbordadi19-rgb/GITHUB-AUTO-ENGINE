import ast
from pathlib import Path

from engine import auto_fixer


def test_repairs_missing_print_parenthesis(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    source = tmp_path / "broken.py"
    source.write_text('print("HELLO"\n', encoding="utf-8")

    assert auto_fixer.repair(source) is True
    assert source.read_text() == 'print("HELLO")\n'
    assert (tmp_path / "engine/backups/broken.py").exists()


def test_valid_file_is_not_modified(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    source = tmp_path / "valid.py"
    original = 'print("VALID")\n'
    source.write_text(original, encoding="utf-8")

    assert auto_fixer.repair(source) is True
    assert source.read_text() == original


def test_unsupported_error_is_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    source = tmp_path / "unsupported.py"
    original = "x = (\n"
    source.write_text(original, encoding="utf-8")

    assert auto_fixer.repair(source) is False
    assert source.read_text() == original


def test_repairs_incomplete_function(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    source = tmp_path / "function.py"
    source.write_text("def hello(\n    pass\n", encoding="utf-8")

    assert auto_fixer.repair(source) is True
    assert source.read_text() == "def hello():\n    pass\n"


def test_rollback_restores_original(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    source = tmp_path / "rollback.py"
    original = 'print("ROLLBACK"\n'
    source.write_text(original, encoding="utf-8")

    real_read_text = Path.read_text
    calls = {"count": 0}

    def failing_read_text(path, *args, **kwargs):
        if path == source:
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("Simulated read failure")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read_text)

    assert auto_fixer.repair(source) is False
    assert real_read_text(source, encoding="utf-8") == original
    ast.parse(original) if False else None
