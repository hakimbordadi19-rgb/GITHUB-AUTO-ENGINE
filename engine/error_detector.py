import ast
import os
import sys
import json
import shutil
import tempfile
import subprocess

CHECKERS = {
    ".php": "PHP",
    ".py": "Python",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".js": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
}

EXCLUDED = {
    ".git", ".venv", "node_modules",
    "__pycache__", "output", "build"
}


def inspect_file(path, language):
    result = {
        "file": path,
        "language": language,
        "status": "OK",
        "errors": []
    }

    try:
        with tempfile.TemporaryDirectory() as temp:
            commands = {
                "PHP": ["php", "-l", path],
                "Python": [sys.executable, "-m", "py_compile", path],

                "Java": [
                    "javac", "-proc:none",
                    "-d", temp, path
                ],

                "C": [
                    "clang", "-fsyntax-only", path
                ],

                "C++": [
                    "clang++", "-fsyntax-only", path
                ],

                "JavaScript": [
                    "node", "--check", path
                ],

                "Go": [
                    "go", "build", "-o",
                    os.path.join(temp, "program"), path
                ],

                "Rust": [
                    "rustc", "--emit=metadata",
                    path, "-o",
                    os.path.join(temp, "program.rmeta")
                ]
            }

            command = commands[language]

            if shutil.which(command[0]) is None:
                result["status"] = "SKIPPED"
                result["errors"].append({
                    "type": "ToolMissing",
                    "message": command[0] + " is not installed"
                })
                return result

            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )

            if process.returncode != 0:
                result["status"] = "ERROR"

                message = (
                    process.stderr or process.stdout
                ).strip()

                error_type = "CompilerError"

                if language == "Python" and "SyntaxError" in message:
                    error_type = "SyntaxError"

                result["errors"].append({
                    "type": error_type,
                    "message": message[:3000]
                })

    except SyntaxError as error:
        result["status"] = "ERROR"
        result["errors"].append({
            "type": "SyntaxError",
            "line": error.lineno,
            "message": error.msg
        })

    except subprocess.TimeoutExpired:
        result["status"] = "ERROR"
        result["errors"].append({
            "type": "Timeout",
            "message": "Inspection exceeded 60 seconds"
        })

    except Exception as error:
        result["status"] = "ERROR"
        result["errors"].append({
            "type": type(error).__name__,
            "message": str(error)
        })

    return result


def scan_project(directories):
    reports = []
    seen = set()

    for directory in directories:
        if not os.path.isdir(directory):
            continue

        for root, dirs, files in os.walk(directory):
            dirs[:] = [
                d for d in dirs
                if d not in EXCLUDED
            ]

            for name in files:
                extension = os.path.splitext(name)[1].lower()

                if extension not in CHECKERS:
                    continue

                path = os.path.join(root, name)

                if path in seen:
                    continue

                seen.add(path)

                language = CHECKERS[extension]
                print(f"[CHECKING] {language}: {path}")

                report = inspect_file(path, language)
                reports.append(report)

                print(f"[{report['status']}] {path}")

    return reports


if __name__ == "__main__":
    reports = scan_project([
        "projects",
        "tests/samples"
    ])

    os.makedirs("logs", exist_ok=True)

    with open("logs/analysis.json", "w", encoding="utf-8") as file:
        json.dump(reports, file, indent=4, ensure_ascii=False)

    success = sum(r["status"] == "OK" for r in reports)
    failed = sum(r["status"] == "ERROR" for r in reports)
    skipped = sum(r["status"] == "SKIPPED" for r in reports)

    print("\n========== ANALYSIS REPORT ==========")
    print("TOTAL:", len(reports))
    print("SUCCESS:", success)
    print("ERRORS:", failed)
    print("SKIPPED:", skipped)
    print("=====================================")

    if failed:
        sys.exit(1)
