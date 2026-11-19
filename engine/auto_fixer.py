import ast
import re
import shutil
import sys
from pathlib import Path


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


def backup(path):
    folder = Path("engine/backups")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / Path(path).name
    shutil.copy2(path, target)
    print("[BACKUP]", target)
    return target


def repair(path):
    file = Path(path)
    source = file.read_text(encoding="utf-8")

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
        lines[index] = re.sub(pattern, r"\\1():", line)

    elif re.match(r"^\\s*print\\(.+\\s*$", line) and not line.rstrip().endswith(")"):
        lines[index] = line + ")"

    else:
        print("[SAFE MODE] No supported repair found.")
        return False

    candidate = "\\n".join(lines) + ("\\n" if source.endswith("\\n") else "")

    try:
        ast.parse(candidate)
    except SyntaxError:
        print("[SAFE MODE] Proposed repair failed validation.")
        return False

    backup_path = backup(path)

    try:
        file.write_text(candidate, encoding="utf-8")
        ast.parse(file.read_text(encoding="utf-8"))

    except Exception as exc:
        shutil.copy2(backup_path, file)
        print("[ROLLBACK] Original file restored.")
        print("[ERROR]", str(exc))
        return False

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
