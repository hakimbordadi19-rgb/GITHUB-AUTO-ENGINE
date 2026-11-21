import re
import shutil
import tempfile
import os
from pathlib import Path

from engine.safe_io import safe_replace


def inspect_javascript(path):
    if not shutil.which("node"):
        return {"status": "SKIPPED", "message": "Node.js missing"}

    result = __import__("subprocess").run(
        ["node", "--check", str(path)],
        capture_output=True,
        text=True,
        timeout=30
    )

    return {
        "status": "OK" if result.returncode == 0 else "ERROR",
        "message": (result.stderr or result.stdout).strip()
    }


def repair_javascript(path):
    file = Path(path)

    if not file.is_file():
        return {"status": "NOT_FOUND"}

    initial = inspect_javascript(file)

    if initial["status"] == "SKIPPED":
        return initial

    if initial["status"] == "OK":
        return {"status": "ALREADY_VALID"}

    source = file.read_text(encoding="utf-8")
    lines = source.splitlines()

    pattern = re.compile(
        r'^(\s*console\.log\("[^"\\\r\n]*"\s*)$'
    )

    repaired = False

    for index, line in enumerate(lines):
        match = pattern.fullmatch(line)
        if match:
            lines[index] = match.group(1) + ")"
            repaired = True
            break

    if not repaired:
        return {"status": "UNSUPPORTED_ERROR"}

    candidate = "\n".join(lines)
    if source.endswith("\n"):
        candidate += "\n"

    temp = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".js",
            dir=file.parent,
            delete=False
        ) as handle:
            handle.write(candidate)
            temp = Path(handle.name)

        validation = inspect_javascript(temp)

        if validation["status"] != "OK":
            return {"status": "VALIDATION_FAILED"}

        backup = safe_replace(
            file,
            candidate,
            backup_dir=file.parent / ".backups"
        )

        final = inspect_javascript(file)

        if final["status"] != "OK":
            shutil.copy2(backup, file)
            return {"status": "ROLLBACK"}

        return {
            "status": "REPAIRED",
            "backup": backup,
            "validation": "OK"
        }

    finally:
        if temp and temp.exists():
            temp.unlink()
