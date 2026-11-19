import os
import subprocess
import sys

BASE = "tests/samples"
OUT = "output/builds"

os.makedirs(OUT, exist_ok=True)

jobs = [
    ("Python", ["python", "-m", "py_compile",
                f"{BASE}/main.py"]),
    ("Java", ["javac", "-d", OUT,
              f"{BASE}/Main.java"]),
    ("C", ["clang", f"{BASE}/main.c",
           "-o", f"{OUT}/main_c"]),
    ("C++", ["clang++", f"{BASE}/main.cpp",
             "-o", f"{OUT}/main_cpp"]),
    ("JavaScript", ["node", "--check",
                    f"{BASE}/main.js"]),
    ("Go", ["go", "build", "-o",
            f"{OUT}/main_go", f"{BASE}/main.go"]),
    ("Rust", ["rustc", f"{BASE}/main.rs",
              "-o", f"{OUT}/main_rust"])
]

success = 0

for name, command in jobs:
    print(f"\n[BUILDING] {name}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            print(f"[SUCCESS] {name}")
            success += 1
        else:
            print(f"[FAILED] {name}")
            print(result.stderr[:1500])

    except Exception as error:
        print(f"[ERROR] {name}: {error}")

print(f"\nBUILD RESULT: {success}/{len(jobs)}")
