import ast
from pathlib import Path

from engine import auto_fixer


def test_repairs_missing_print_parenthesis(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    source = tmp_path / "broken.py"
    source.write_text('print("HELLO"\n', encoding="utf-8")

    assert auto_fixer.repair(source) is True
    assert source.read_text() == 'print("HELLO")\n'

    backups = list((tmp_path / ".backups").glob("broken.py.*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == 'print("HELLO"\n'

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


def test_inspect_valid_file(tmp_path, capsys):
    source = tmp_path / "valid.py"
    source.write_text('print("OK")\n', encoding="utf-8")

    assert auto_fixer.inspect(source) is True
    assert "[OK]" in capsys.readouterr().out


def test_inspect_invalid_file(tmp_path, capsys):
    source = tmp_path / "broken.py"
    source.write_text("print(\n", encoding="utf-8")

    assert auto_fixer.inspect(source) is False
    output = capsys.readouterr().out

    assert "[ERROR]" in output
    assert "Line:" in output
    assert "Problem:" in output


def test_repair_handles_read_error(tmp_path, monkeypatch, capsys):
    source = tmp_path / "unreadable.py"
    source.write_text("print(\n")

    def fail_read(*args, **kwargs):
        raise OSError("Read failed")

    monkeypatch.setattr(Path, "read_text", fail_read)

    assert auto_fixer.repair(source) is False
    assert "Read failed" in capsys.readouterr().out


def test_repair_handles_unknown_error_line(tmp_path, monkeypatch):
    source = tmp_path / "unknown.py"
    source.write_text("broken\n")

    def fake_parse(code):
        raise SyntaxError("Unknown line", ("unknown.py", None, None, None))

    monkeypatch.setattr(auto_fixer.ast, "parse", fake_parse)

    assert auto_fixer.repair(source) is False


def test_repair_handles_invalid_error_location(tmp_path, monkeypatch):
    source = tmp_path / "location.py"
    source.write_text("print(\n")

    def fake_parse(code):
        raise SyntaxError("Invalid line", ("location.py", 99, 1, "print("))

    monkeypatch.setattr(auto_fixer.ast, "parse", fake_parse)

    assert auto_fixer.repair(source) is False


def test_repair_rejects_invalid_candidate(tmp_path, monkeypatch):
    source = tmp_path / "candidate.py"
    source.write_text("print(\n")

    calls = {"count": 0}

    def fake_parse(code):
        calls["count"] += 1
        if calls["count"] == 1:
            raise SyntaxError("Original error", ("candidate.py", 1, 1, "print("))
        raise SyntaxError("Candidate still invalid")

    monkeypatch.setattr(auto_fixer.ast, "parse", fake_parse)

    assert auto_fixer.repair(source) is False
    assert source.read_text() == "print(\n"


def test_rollback_failure_is_reported(tmp_path, monkeypatch, capsys):
    source = tmp_path / "rollback_failed.py"
    original = 'print("ROLLBACK"\n'
    source.write_text(original, encoding="utf-8")

    real_read_text = Path.read_text
    calls = {"count": 0}

    def failing_read(path, *args, **kwargs):
        if path == source:
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("Simulated read failure")
        return real_read_text(path, *args, **kwargs)

    def failing_restore(*args, **kwargs):
        raise OSError("Simulated restore failure")

    monkeypatch.setattr(Path, "read_text", failing_read)
    monkeypatch.setattr(auto_fixer, "safe_restore", failing_restore)

    assert auto_fixer.repair(source) is False
    assert "[ROLLBACK FAILED]" in capsys.readouterr().out
