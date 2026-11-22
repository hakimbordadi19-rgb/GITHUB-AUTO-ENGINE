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
    except SyntaxError as e:
        print("[ERROR]", path)
        print("Line:", e.lineno)
        print("Problem:", e.msg)
        return False


def repair(path):
    file = Path(path)

    try:
        source = file.read_text(encoding="utf-8")
    except OSError as exc:
        print("[ERROR]", str(exc))
        return False

    try:
        ast.parse(source)
        print("[READY] No repair needed.")
        return True
    except SyntaxError as exc:
        error_line = exc.lineno

    lines = source.splitlines()

    if not error_line:
        print("[SAFE MODE] Cannot identify the error line.")
        return False

    index = error_line - 1

    if index >= len(lines):
        print("[SAFE MODE] Invalid error location.")
        return False

    pattern = r"^(\s*def\s+[A-Za-z_]\w*)\(\s*$"
    line = lines[index]

    if re.match(pattern, line):
        lines[index] = re.sub(pattern, r"\1():", line)

    elif re.match(r"^\s*print\(.+\s*$", line) and not line.rstrip().endswith(")"):
        lines[index] = line + ")"

    else:
        print("[SAFE MODE] No supported repair found.")
        return False

    candidate = "\n".join(lines) + ("\n" if source.endswith("\n") else "")

    try:
        ast.parse(candidate)
    except SyntaxError:
        print("[SAFE MODE] Proposed repair failed validation.")
        return False

    backup_path = None

    try:
        backup_path = safe_replace(
            file,
            candidate,
            backup_dir=file.parent / ".backups"
        )

        ast.parse(file.read_text(encoding="utf-8"))

    except Exception as exc:
        if backup_path is not None:
            try:
                safe_restore(file, backup_path)
                print("[ROLLBACK] Original file restored.")
            except Exception as restore_exc:
                print("[ROLLBACK FAILED]", str(restore_exc))

        print("[ERROR]", str(exc))
        return False

    print("[BACKUP]", backup_path)
    print("[FIXED]", path)
    print("[VALIDATION] Python syntax OK")
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "projects/sample/main.py"

    if Path(path).is_file():
        if not repair(path):
            print("[NEXT] Manual review required.")
    else:
        print("[ERROR] File not found:", path)
