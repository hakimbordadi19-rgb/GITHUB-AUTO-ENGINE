
import ast
import os
import json

def inspect_file(path):
    result = {
        "file": path,
        "language": "Python",
        "status": "OK",
        "errors": []
    }

    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()

        ast.parse(source)

    except SyntaxError as e:
        result["status"] = "ERROR"
        result["errors"].append({
            "type": "SyntaxError",
            "line": e.lineno,
            "message": e.msg
        })

    except Exception as e:
        result["status"] = "ERROR"
        result["errors"].append({
            "type": type(e).__name__,
            "message": str(e)
        })

    return result


def scan_project(directory):
    reports = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [
            d for d in dirs
            if d not in [".git", ".venv", "node_modules"]
        ]

        for name in files:
            if name.endswith(".py"):
                path = os.path.join(root, name)
                reports.append(inspect_file(path))

    return reports


if __name__ == "__main__":
    reports = scan_project("projects")

    os.makedirs("logs", exist_ok=True)

    with open("logs/analysis.json", "w") as f:
        json.dump(reports, f, indent=4)

    for report in reports:
        print(report["status"], report["file"])
        for error in report["errors"]:
            print("  ERROR:", error)

    print("\nSCAN COMPLETED")
