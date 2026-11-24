from engine.integration_engine import run_project


def test_run_project_missing_path(tmp_path):
    missing = tmp_path / "missing_project"

    result = run_project(missing)

    assert result["status"] == "NOT_FOUND"
    assert result["files_scanned"] == 0
    assert result["results"] == []

def test_run_project_single_file(tmp_path, monkeypatch):
    file = tmp_path / "main.py"
    file.write_text('print("hello")\n', encoding="utf-8")

    def fake_repair(path):
        return {
            "status": "REPAIRED",
            "repair_success": True,
            "final_status": "OK"
        }

    monkeypatch.setattr(
        "engine.integration_engine.intelligent_repair",
        fake_repair
    )

    result = run_project(file)

    assert result["status"] == "COMPLETED"
    assert result["files_scanned"] == 1
    assert result["repaired"] == 1
    assert result["failed"] == 0
    assert len(result["results"]) == 1

def test_run_project_scans_multiple_files(tmp_path, monkeypatch):
    (tmp_path / "main.py").write_text("print(1)")
    (tmp_path / "app.js").write_text("console.log(1)")
    (tmp_path / "readme.txt").write_text("documentation")

    calls = []

    def fake_repair(path):
        calls.append(path)
        return {
            "status": "REPAIRED",
            "repair_success": True,
            "final_status": "OK"
        }

    monkeypatch.setattr(
        "engine.integration_engine.intelligent_repair",
        fake_repair
    )

    result = run_project(tmp_path)

    assert result["status"] == "COMPLETED"
    assert result["files_scanned"] == 2
    assert result["files_ignored"] == 1
    assert result["repaired"] == 2
    assert len(calls) == 2
    assert result["languages"] == {
        "Python": 1,
        "JavaScript": 1
    }
def test_run_project_ignores_excluded_directories(tmp_path, monkeypatch):
    (tmp_path / "main.py").write_text("print(1)")

    excluded = tmp_path / ".venv"
    excluded.mkdir()
    (excluded / "hidden.py").write_text("print(2)")

    calls = []

    def fake_repair(path):
        calls.append(path)
        return {"status": "REPAIRED"}

    monkeypatch.setattr(
        "engine.integration_engine.intelligent_repair",
        fake_repair
    )

    result = run_project(tmp_path)

    assert result["files_scanned"] == 1
    assert len(calls) == 1
    assert result["repaired"] == 1

def test_run_project_unsupported_file(tmp_path):
    file = tmp_path / "README.txt"
    file.write_text("Documentation")

    result = run_project(file)

    assert result["status"] == "COMPLETED"
    assert result["files_scanned"] == 0
    assert result["files_ignored"] == 1
    assert result["results"] == []

def test_run_project_counts_failed_repairs(tmp_path, monkeypatch):
    file = tmp_path / "broken.py"
    file.write_text("invalid code")

    def fake_repair(path):
        return {"status": "REPAIR_FAILED"}

    monkeypatch.setattr(
        "engine.integration_engine.intelligent_repair",
        fake_repair
    )

    result = run_project(file)

    assert result["files_scanned"] == 1
    assert result["failed"] == 1
    assert result["repaired"] == 0
def test_run_project_counts_manual_review(tmp_path, monkeypatch):
    file = tmp_path / "uncertain.py"
    file.write_text("print('test')")

    def fake_repair(path):
        return {"status": "MANUAL_REVIEW_REQUIRED"}

    monkeypatch.setattr(
        "engine.integration_engine.intelligent_repair",
        fake_repair
    )

    result = run_project(file)

    assert result["files_scanned"] == 1
    assert result["manual_review"] == 1
    assert result["repaired"] == 0
    assert result["failed"] == 0
def test_run_project_report_metadata(tmp_path, monkeypatch):
    file = tmp_path / "main.py"
    file.write_text("print(1)")

    monkeypatch.setattr(
        "engine.integration_engine.intelligent_repair",
        lambda path: {"status": "REPAIRED"}
    )

    result = run_project(tmp_path)

    assert result["engine"] == "GITHUB-AUTO-ENGINE"
    assert result["target"] == str(tmp_path)
    assert result["status"] == "COMPLETED"
    assert isinstance(result["results"], list)
    assert isinstance(result["languages"], dict)
def test_run_project_counts_exceptions(tmp_path, monkeypatch):
    file = tmp_path / "crash.py"
    file.write_text("print(1)")

    def fake_repair(path):
        return {"status": "EXCEPTION"}

    monkeypatch.setattr(
        "engine.integration_engine.intelligent_repair",
        fake_repair
    )

    result = run_project(file)

    assert result["files_scanned"] == 1
    assert result["failed"] == 1
    assert result["repaired"] == 0
def test_missing_path_report_counters(tmp_path):
    missing = tmp_path / "unknown"

    result = run_project(missing)

    assert result["files_scanned"] == 0
    assert result["files_ignored"] == 0
    assert result["repaired"] == 0
    assert result["failed"] == 0
    assert result["manual_review"] == 0
    assert result["languages"] == {}

def test_run_project_ignores_file_inside_excluded_directory(
    tmp_path, monkeypatch
):
    excluded = tmp_path / ".venv"
    excluded.mkdir()

    file = excluded / "hidden.py"
    file.write_text("print(1)")

    calls = []

    def fake_repair(path):
        calls.append(path)
        return {"status": "REPAIRED"}

    monkeypatch.setattr(
        "engine.integration_engine.intelligent_repair",
        fake_repair
    )

    result = run_project(file)

    assert len(calls) == 0
    assert result["files_scanned"] == 0
