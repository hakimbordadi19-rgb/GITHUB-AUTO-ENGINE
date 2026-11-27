import os
import subprocess

BASE = "tests/samples"
OUT = "output/builds"


def get_jobs():
    return [
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
                  "-o", f"{OUT}/main_rust"]),
    ]


def build_all():
    os.makedirs(OUT, exist_ok=True)
    jobs = get_jobs()
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

        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {name}")

        except Exception as error:
            print(f"[ERROR] {name}: {error}")

    print(f"\nBUILD RESULT: {success}/{len(jobs)}")
    return {
        "success": success,
        "total": len(jobs),
        "failed": len(jobs) - success,
    }


def main():
    build_all()


if __name__ == "__main__":
    main()
