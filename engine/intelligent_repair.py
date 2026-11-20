from pathlib import Path

from engine.analyzer import LANGUAGES
from engine.error_detector import inspect_file
from engine.auto_fixer import repair


def intelligent_repair(path):
    file = Path(path)

    report = {
        "file": str(file),
        "status": "UNKNOWN",
        "language": None,
        "initial_errors": [],
        "repair_attempted": False,
        "repair_success": False,
        "final_status": None
    }

    if not file.is_file():
        report["status"] = "NOT_FOUND"
        return report

    language = LANGUAGES.get(file.suffix.lower())

    if not language:
        report["status"] = "UNSUPPORTED"
        return report

    report["language"] = language

    initial = inspect_file(str(file), language)

    report["initial_errors"] = initial["errors"]

    if initial["status"] == "OK":
        report["status"] = "ALREADY_CLEAN"
        report["final_status"] = "OK"
        return report

    if initial["status"] == "SKIPPED":
        report["status"] = "CHECKER_UNAVAILABLE"
        report["final_status"] = "SKIPPED"
        return report

    # Auto Fixer currently supports Python syntax repairs only.
    if language != "Python":
        report["status"] = "MANUAL_REVIEW_REQUIRED"
        report["final_status"] = "ERROR"
        return report

    report["repair_attempted"] = True

    try:
        success = repair(str(file))
        report["repair_success"] = bool(success)

        final = inspect_file(str(file), language)
        report["final_status"] = final["status"]

        if final["status"] == "OK":
            report["status"] = "REPAIRED"
        else:
            report["status"] = "REPAIR_FAILED"

    except Exception as error:
        report["status"] = "EXCEPTION"
        report["exception"] = str(error)

    return report


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m engine.intelligent_repair FILE")
        raise SystemExit(2)

    result = intelligent_repair(sys.argv[1])
    print(json.dumps(result, indent=4, ensure_ascii=False))
