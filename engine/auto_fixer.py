
import ast
import re
import sys
from pathlib import Path

from engine.safe_io import safe_replace, safe_restore


def inspect(path):
    try:
        ast.parse(Path(path).read_text(encoding="utf-8"))
        print("[OK]", path)
        return True
    except SyntaxError as exc:
        print("[ERROR]", path)
        print("Line:", exc.lineno)
        print("Problem:", exc.msg)
        return False


def repair_detailed(path):
    file = Path(path)

    report = {
        "file": str(file),
        "status": "UNKNOWN",
        "backup": None,
        "error": None,
        "rollback_attempted": False,
        "rollback_success": None,
    }

    try:
        source = file.read_text(encoding="utf-8")
    except OSError as exc:
        report.update(status="NOT_FOUND", error=str(exc))
        print("[ERROR]", str(exc))
        return report

    try:
        ast.parse(source)
        report["status"] = "ALREADY_CLEAN"
        print("[READY] No repair needed.")
        return report
    except SyntaxError as exc:
        error_line = exc.lineno

    lines = source.splitlines()

    if not error_line:
        report["status"] = "MANUAL_REVIEW_REQUIRED"
        print("[SAFE MODE] Cannot identify the error line.")
        return report

    index = error_line - 1

    if index < 0 or index >= len(lines):
        report["status"] = "MANUAL_REVIEW_REQUIRED"
        print("[SAFE MODE] Invalid error location.")
        return report

    pattern = r"^(\s*def\s+[A-Za-z_]\w*)\(\s*$"
    line = lines[index]

    if re.match(pattern, line):
        lines[index] = re.sub(pattern, r"\1():", line)

    elif re.match(r"^\s*print\(.+\s*$", line) and not line.rstrip().endswith(")"):
        lines[index] = line + ")"

    else:
        report["status"] = "MANUAL_REVIEW_REQUIRED"
        print("[SAFE MODE] No supported repair found.")
        return report

    candidate = "\n".join(lines) + ("\n" if source.endswith("\n") else "")

    try:
        ast.parse(candidate)
    except SyntaxError as exc:
        report.update(
            status="REPAIR_FAILED",
            error=str(exc),
        )
        print("[SAFE MODE] Proposed repair failed validation.")
        return report

    backup_path = None

    try:
        backup_path = safe_replace(
            file,
            candidate,
            backup_dir=file.parent / ".backups"
        )

        report["backup"] = str(backup_path)

        ast.parse(file.read_text(encoding="utf-8"))

    except Exception as exc:
        report["error"] = str(exc)

        if backup_path is not None:
            report["rollback_attempted"] = True

            try:
                safe_restore(file, backup_path)
                report["rollback_success"] = True
                print("[ROLLBACK] Original file restored.")

            except Exception as restore_exc:
                report["rollback_success"] = False
                report["status"] = "ROLLBACK_FAILED"
                report["error"] = str(restore_exc)
                print("[ROLLBACK FAILED]", str(restore_exc))
                return report

        report["status"] = "REPAIR_FAILED"
        print("[ERROR]", str(exc))
        return report

    report["status"] = "REPAIRED"

    print("[BACKUP]", backup_path)
    print("[FIXED]", path)
    print("[VALIDATION] Python syntax OK")

    return report


def repair(path):
    """Backward-compatible Boolean interface."""
    result = repair_detailed(path)
    return result["status"] in ("REPAIRED", "ALREADY_CLEAN")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "projects/sample/main.py"

    if Path(path).is_file():
        result = repair_detailed(path)

        if result["status"] not in ("REPAIRED", "ALREADY_CLEAN"):
            print("[NEXT] Manual review required.")
    else:
        print("[ERROR] File not found:", path)
