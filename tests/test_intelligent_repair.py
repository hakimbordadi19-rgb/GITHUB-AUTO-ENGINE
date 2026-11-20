from engine import intelligent_repair as engine


def test_missing_file():
    result = engine.intelligent_repair("missing.py")
    assert result["status"] == "NOT_FOUND"


def test_unsupported_language(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("hello")

    result = engine.intelligent_repair(str(file))
    assert result["status"] == "UNSUPPORTED"


def test_already_clean(tmp_path, monkeypatch):
    file = tmp_path / "clean.py"
    file.write_text("print('OK')")

    monkeypatch.setattr(
        engine, "inspect_file",
        lambda *args: {"status": "OK", "errors": []}
    )

    result = engine.intelligent_repair(str(file))
    assert result["status"] == "ALREADY_CLEAN"


def test_checker_unavailable(tmp_path, monkeypatch):
    file = tmp_path / "test.py"
    file.write_text("print('OK')")

    monkeypatch.setattr(
        engine, "inspect_file",
        lambda *args: {"status": "SKIPPED", "errors": []}
    )

    result = engine.intelligent_repair(str(file))
    assert result["status"] == "CHECKER_UNAVAILABLE"


def test_non_python_requires_manual_review(tmp_path, monkeypatch):
    file = tmp_path / "test.js"
    file.write_text("invalid code")

    monkeypatch.setattr(
        engine, "inspect_file",
        lambda *args: {"status": "ERROR", "errors": [{"type": "CompilerError"}]}
    )

    result = engine.intelligent_repair(str(file))
    assert result["status"] == "MANUAL_REVIEW_REQUIRED"


def test_successful_repair(tmp_path, monkeypatch):
    file = tmp_path / "broken.py"
    file.write_text("broken code")

    calls = {"count": 0}

    def fake_inspect(path, language):
        calls["count"] += 1

        if calls["count"] == 1:
            return {"status": "ERROR", "errors": [{"type": "SyntaxError"}]}

        return {"status": "OK", "errors": []}

    monkeypatch.setattr(engine, "inspect_file", fake_inspect)
    monkeypatch.setattr(engine, "repair", lambda path: True)

    result = engine.intelligent_repair(str(file))

    assert result["status"] == "REPAIRED"
    assert result["final_status"] == "OK"


def test_repair_failure(tmp_path, monkeypatch):
    file = tmp_path / "broken.py"
    file.write_text("broken code")

    monkeypatch.setattr(
        engine, "inspect_file",
        lambda *args: {"status": "ERROR", "errors": []}
    )
    monkeypatch.setattr(engine, "repair", lambda path: False)

    result = engine.intelligent_repair(str(file))

    assert result["status"] == "REPAIR_FAILED"


def test_repair_exception(tmp_path, monkeypatch):
    file = tmp_path / "broken.py"
    file.write_text("broken code")

    monkeypatch.setattr(
        engine, "inspect_file",
        lambda *args: {"status": "ERROR", "errors": []}
    )

    def raise_error(path):
        raise RuntimeError("Test exception")

    monkeypatch.setattr(engine, "repair", raise_error)

    result = engine.intelligent_repair(str(file))

    assert result["status"] == "EXCEPTION"
