from engine.analyzer import analyze


def test_analyze_detects_supported_languages(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "index.php").write_text("<?php")
    (tmp_path / "app.js").write_text("console.log('hello')")
    (tmp_path / "readme.txt").write_text("text")

    results = analyze(tmp_path)

    languages = {item["language"] for item in results}

    assert languages == {"Python", "PHP", "JavaScript"}
    assert len(results) == 3


def test_analyze_ignores_excluded_directories(tmp_path):
    (tmp_path / "main.py").write_text("print(1)")

    for folder in [".git", "node_modules", ".venv", "build"]:
        directory = tmp_path / folder
        directory.mkdir()
        (directory / "hidden.py").write_text("print(2)")

    results = analyze(tmp_path)

    assert len(results) == 1
    assert results[0]["language"] == "Python"


def test_analyze_missing_directory_returns_empty(tmp_path):
    missing = tmp_path / "missing"

    assert analyze(missing) == []


def test_analyzer_main_execution(tmp_path, monkeypatch, capsys):
    import runpy
    from pathlib import Path

    project_dir = tmp_path / "projects"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('hello')")

    monkeypatch.chdir(tmp_path)

    script = Path(__file__).resolve().parents[1] / "engine" / "analyzer.py"
    runpy.run_path(str(script), run_name="__main__")

    output = capsys.readouterr().out

    assert '"language": "Python"' in output
    assert "Files analyzed: 1" in output
