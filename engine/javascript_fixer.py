import re
import shutil
import subprocess
import hashlib
from pathlib import Path


def inspect_javascript(path):
    if not shutil.which("node"):
        return {"status": "SKIPPED", "message": "Node.js missing"}

    result = subprocess.run(
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

    temp = file.with_name(file.stem + ".repair.tmp" + file.suffix)

    try:
        temp.write_text(candidate, encoding="utf-8")
        validation = inspect_javascript(temp)

        if validation["status"] != "OK":
            return {"status": "VALIDATION_FAILED"}

        digest = hashlib.sha256(
            str(file.resolve()).encode()
        ).hexdigest()[:12]

        backup_dir = Path("engine/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup = backup_dir / f"{file.name}.{digest}.bak"

        if backup.exists():
            return {"status": "BACKUP_EXISTS"}

        shutil.copy2(file, backup)

        try:
            file.write_text(candidate, encoding="utf-8")

            final = inspect_javascript(file)

            if final["status"] != "OK":
                shutil.copy2(backup, file)
                return {"status": "ROLLBACK"}

        except Exception:
            shutil.copy2(backup, file)
            raise

        return {
            "status": "REPAIRED",
            "backup": str(backup),
            "validation": "OK"
        }

    finally:
        if temp.exists():
            temp.unlink()
