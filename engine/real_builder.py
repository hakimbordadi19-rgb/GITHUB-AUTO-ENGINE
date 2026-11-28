
import os
import sys
import shutil
import subprocess
from pathlib import Path


BASE = "tests/samples"
OUT = "output/builds"

BUILDERS = {
    "Python": "python",
    "Java": "java",
    "C": "c",
    "C++": "cpp",
    "JavaScript": "js",
    "Go": "go",
    "Rust": "rs",
}


def get_jobs():
    return [
        ("Python", ["python", "-m", "py_compile",
                    f"{BASE}/main.py"]),
        ("Java", ["javac", "-d", OUT, f"{BASE}/Main.java"]),
        ("C", ["clang", f"{BASE}/main.c", "-o", f"{OUT}/main_c"]),
        ("C++", ["clang++", f"{BASE}/main.cpp", "-o", f"{OUT}/main_cpp"]),
        ("JavaScript", ["node", "--check", f"{BASE}/main.js"]),
        ("Go", ["go", "build", "-o", f"{OUT}/main_go",
                f"{BASE}/main.go"]),
        ("Rust", ["rustc", f"{BASE}/main.rs", "-o", f"{OUT}/main_rust"]),
    ]



def build_file(path, language, output_dir=OUT):
    source = Path(path)

    result = {
        "file": str(source),
        "language": language,
        "status": "FAILED",
        "output": None,
        "artifact_type": None,
        "error": None,
    }

    tools = {
        "Python": "python",
        "Java": "javac",
        "C": "clang",
        "C++": "clang++",
        "JavaScript": "node",
        "Go": "go",
        "Rust": "rustc",
    }

    if not source.is_file():
        result["status"] = "NOT_FOUND"
        result["error"] = "Source file not found"
        return result

    if language not in tools:
        result["status"] = "UNSUPPORTED"
        result["error"] = "Unsupported language"
        return result

    tool = tools[language]

    if shutil.which(tool) is None:
        result["status"] = "CHECKER_UNAVAILABLE"
        result["error"] = f"{tool} is not installed"
        return result

    try:
        base_output = Path(output_dir)
        lang_output = base_output / language.lower().replace("+", "p")

        lang_output.mkdir(parents=True, exist_ok=True)

        destination = lang_output / source.stem

        if language == "Python":
            destination = destination.with_suffix(".pyc")
            command = [
                sys.executable,
                "-c",
                "import py_compile,sys; "
                "py_compile.compile(sys.argv[1], "
                "cfile=sys.argv[2], doraise=True)",
                str(source),
                str(destination),
            ]
            artifact_type = "bytecode"

        elif language == "Java":
            command = [
                "javac", "-proc:none",
                "-d", str(lang_output),
                str(source),
            ]
            destination = lang_output
            artifact_type = "class_files"

        elif language == "C":
            command = [
                "clang", str(source),
                "-o", str(destination),
            ]
            artifact_type = "executable"

        elif language == "C++":
            command = [
                "clang++", str(source),
                "-o", str(destination),
            ]
            artifact_type = "executable"

        elif language == "JavaScript":
            command = ["node", "--check", str(source)]
            destination = None
            artifact_type = "syntax_check"

        elif language == "Go":
            command = [
                "go", "build",
                "-o", str(destination),
                str(source),
            ]
            artifact_type = "executable"

        else:
            command = [
                "rustc", str(source),
                "-o", str(destination),
            ]
            artifact_type = "executable"

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if process.returncode == 0:
            result["status"] = "SUCCESS"
            result["output"] = (
                str(destination) if destination else None
            )
            result["artifact_type"] = artifact_type
        else:
            result["error"] = (
                process.stderr or process.stdout
            )[:3000]

    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["error"] = "Build exceeded 120 seconds"

    except Exception as error:
        result["status"] = "ERROR"
        result["error"] = str(error)

    return result


def build_all():
    jobs = get_jobs()
    success = 0

    for name, command in jobs:
        print(f"\n[BUILDING] {name}")

        source_file = command[-1]
        result = build_file(source_file, name)

        if result["status"] == "SUCCESS":
            print(f"[SUCCESS] {name}")
            success += 1
        else:
            if result["error"]:
                print(
                    f"[{result['status']}] {name}: "
                    f"{result['error'][:1500]}"
                )
            else:
                print(f"[{result['status']}] {name}")

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
