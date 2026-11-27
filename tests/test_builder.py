from types import SimpleNamespace

from engine import real_builder


def test_get_jobs_contains_seven_languages():
    jobs = real_builder.get_jobs()

    assert len(jobs) == 7
    assert [name for name, command in jobs] == [
        "Python",
        "Java",
        "C",
        "C++",
        "JavaScript",
        "Go",
        "Rust",
    ]


def test_build_all_success(monkeypatch, capsys):
    monkeypatch.setattr(real_builder.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(
        real_builder.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stderr=""),
    )

    result = real_builder.build_all()

    assert result == {"success": 7, "total": 7, "failed": 0}
    assert "BUILD RESULT: 7/7" in capsys.readouterr().out


def test_build_all_handles_compiler_failure(monkeypatch, capsys):
    monkeypatch.setattr(real_builder.os, "makedirs", lambda *a, **k: None)
    calls = {"count": 0}

    def fake_run(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return SimpleNamespace(returncode=1, stderr="compiler error")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(real_builder.subprocess, "run", fake_run)

    result = real_builder.build_all()

    assert result == {"success": 6, "total": 7, "failed": 1}
    output = capsys.readouterr().out
    assert "[FAILED] Python" in output
    assert "compiler error" in output


def test_build_all_handles_timeout(monkeypatch, capsys):
    monkeypatch.setattr(real_builder.os, "makedirs", lambda *a, **k: None)

    calls = {"count": 0}

    def fake_run(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise real_builder.subprocess.TimeoutExpired(
                cmd=args[0],
                timeout=kwargs["timeout"],
            )
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(real_builder.subprocess, "run", fake_run)

    result = real_builder.build_all()

    assert result == {"success": 6, "total": 7, "failed": 1}
    assert "[TIMEOUT] Python" in capsys.readouterr().out


def test_build_all_continues_after_exception(monkeypatch, capsys):
    monkeypatch.setattr(real_builder.os, "makedirs", lambda *a, **k: None)

    calls = {"count": 0}

    def fake_run(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("simulated error")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(real_builder.subprocess, "run", fake_run)

    result = real_builder.build_all()

    assert result == {"success": 6, "total": 7, "failed": 1}
    assert "[ERROR] Python: simulated error" in capsys.readouterr().out


def test_check_tools_all_available(monkeypatch, capsys):
    from engine import builder

    monkeypatch.setattr(builder.shutil, "which", lambda name: "/fake/" + name)
    monkeypatch.setattr(
        builder.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout="Tool version 1.0", stderr=""
        ),
    )

    result = builder.check_tools()

    assert len(result) == 6
    assert all(result.values())
    assert "[AVAILABLE]" in capsys.readouterr().out


def test_check_tools_missing_compiler(monkeypatch, capsys):
    from engine import builder

    monkeypatch.setattr(
        builder.shutil, "which",
        lambda name: None if name == "javac" else "/fake/" + name,
    )
    monkeypatch.setattr(
        builder.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout="version", stderr=""
        ),
    )

    result = builder.check_tools()

    assert result["Java"] is False
    assert "[MISSING] Java" in capsys.readouterr().out


def test_check_tools_command_failure(monkeypatch, capsys):
    from engine import builder

    monkeypatch.setattr(builder.shutil, "which", lambda name: "/fake/" + name)
    monkeypatch.setattr(
        builder.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=1, stdout="", stderr="version error"
        ),
    )

    result = builder.check_tools()

    assert not any(result.values())
    assert "[ERROR]" in capsys.readouterr().out


def test_check_tools_timeout(monkeypatch, capsys):
    from engine import builder

    monkeypatch.setattr(builder.shutil, "which", lambda name: "/fake/" + name)

    def fake_run(command, **kwargs):
        if command[0] == "python":
            raise builder.subprocess.TimeoutExpired(command, 10)
        return SimpleNamespace(
            returncode=0, stdout="version", stderr=""
        )

    monkeypatch.setattr(builder.subprocess, "run", fake_run)

    result = builder.check_tools()

    assert result["Python"] is False
    assert result["Java"] is True
    assert "[TIMEOUT] Python" in capsys.readouterr().out
