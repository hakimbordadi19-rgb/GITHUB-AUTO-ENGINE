import ast
import os
import shutil
import sys

def inspect(path):
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()

        ast.parse(source)
        print("[OK]", path)
        return True

    except SyntaxError as e:
        print("[ERROR]", path)
        print("Line:", e.lineno)
        print("Problem:", e.msg)
        return False

def backup(path):
    os.makedirs("engine/backups", exist_ok=True)
    name = os.path.basename(path)
    target = os.path.join("engine/backups", name)
    shutil.copy2(path, target)
    print("[BACKUP]", target)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "projects/sample/main.py"

    if os.path.isfile(path):
        if not inspect(path):
            print("[SAFE MODE] No automatic changes made.")
            print("[NEXT] Manual review required.")
        else:
            print("[READY] No repair needed.")
    else:
        print("[ERROR] File not found:", path)
