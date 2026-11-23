from pathlib import Path
import os

from engine.safe_io import safe_replace, safe_restore


def test_safe_replace_creates_backup(tmp_path):
    file = tmp_path / "test.py"
    file.write_text("ORIGINAL")

    backup = safe_replace(
        file,
        "FIXED",
        backup_dir=tmp_path / "backups"
    )

    assert file.read_text() == "FIXED"
    assert os.path.isfile(backup)

    with open(backup) as f:
        assert f.read() == "ORIGINAL"


def test_safe_restore_recovers_original(tmp_path):
    file = tmp_path / "test.py"
    file.write_text("ORIGINAL")

    backup = safe_replace(
        file,
        "FIXED",
        backup_dir=tmp_path / "backups"
    )

    safe_restore(file, backup)

    assert file.read_text() == "ORIGINAL"


def test_safe_replace_rolls_back_on_failure(
    tmp_path, monkeypatch
):
    import engine.safe_io as safe_io

    file = tmp_path / "test.py"
    file.write_text("ORIGINAL")

    real_replace = os.replace
    calls = {"count": 0}

    def failing_replace(src, dst):
        calls["count"] += 1

        if calls["count"] == 1:
            raise OSError("Simulated replacement failure")

        return real_replace(src, dst)

    monkeypatch.setattr(
        safe_io.os, "replace", failing_replace
    )

    try:
        safe_io.safe_replace(
            file,
            "FIXED",
            backup_dir=tmp_path / "backups"
        )
        assert False, "Expected OSError"
    except OSError:
        pass

    assert file.read_text() == "ORIGINAL"


def test_safe_replace_preserves_file_permissions(tmp_path):
    file = tmp_path / "permissions.py"
    file.write_text("ORIGINAL")
    file.chmod(0o640)

    safe_replace(
        file,
        "FIXED",
        backup_dir=tmp_path / "backups"
    )

    assert file.stat().st_mode & 0o777 == 0o640


def test_safe_replace_backup_preserves_permissions(tmp_path):
    file = tmp_path / "backup_permissions.py"
    file.write_text("ORIGINAL")
    file.chmod(0o640)

    backup = safe_replace(
        file,
        "FIXED",
        backup_dir=tmp_path / "backups"
    )

    assert Path(backup).stat().st_mode & 0o777 == 0o640

def test_safe_restore_cleans_temp_file_on_failure(
    tmp_path, monkeypatch
):
    import engine.safe_io as safe_io

    file = tmp_path / "test.py"
    file.write_text("FIXED")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    backup = backup_dir / "original.bak"
    backup.write_text("ORIGINAL")

    def failing_replace(src, dst):
        raise OSError("Simulated restore failure")

    monkeypatch.setattr(
        safe_io.os, "replace", failing_replace
    )

    try:
        safe_io.safe_restore(file, backup)
        assert False, "Expected OSError"
    except OSError:
        pass

    assert file.read_text() == "FIXED"
    assert not list(tmp_path.glob(".restore_*"))
