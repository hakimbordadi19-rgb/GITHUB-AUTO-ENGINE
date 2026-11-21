import os
import shutil
import tempfile
import uuid
from pathlib import Path


def safe_replace(path, content, backup_dir="engine/backups"):
    file = Path(path)

    if not file.is_file():
        raise FileNotFoundError(file)

    backup_folder = Path(backup_dir)
    backup_folder.mkdir(parents=True, exist_ok=True)

    backup = backup_folder / (
        f"{file.name}.{uuid.uuid4().hex[:12]}.bak"
    )

    shutil.copy2(file, backup)
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=file.parent,
            delete=False
        ) as temp:
            temp.write(content)
            temp.flush()
            os.fsync(temp.fileno())
            temp_path = Path(temp.name)

        os.chmod(temp_path, file.stat().st_mode)
        os.replace(temp_path, file)

        return str(backup)

    except Exception:
        if temp_path and temp_path.exists():
            temp_path.unlink()

        restore_fd, restore_name = tempfile.mkstemp(
            dir=file.parent,
            prefix=".restore_"
        )
        os.close(restore_fd)
        restore_path = Path(restore_name)

        try:
            shutil.copy2(backup, restore_path)
            os.replace(restore_path, file)
        finally:
            if restore_path.exists():
                restore_path.unlink()

        raise

def safe_restore(path, backup_path):
    file = Path(path)
    backup = Path(backup_path)

    if not backup.is_file():
        raise FileNotFoundError(backup)

    restore_fd, restore_name = tempfile.mkstemp(
        dir=file.parent,
        prefix=".restore_"
    )
    os.close(restore_fd)
    restore_path = Path(restore_name)

    try:
        shutil.copy2(backup, restore_path)
        os.replace(restore_path, file)
    finally:
        if restore_path.exists():
            restore_path.unlink()
