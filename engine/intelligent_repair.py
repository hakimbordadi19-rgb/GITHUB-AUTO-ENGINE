from pathlib import Path

from engine.analyzer import LANGUAGES
from engine.error_detector import inspect_file
from engine.auto_fixer import repair
from engine.javascript_fixer import repair_javascript
from engine.php_fixer import repair_php


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

    report["repair_attempted"] = True

    try:
        if language == "Python":
            success = repair(str(file))

            final = inspect_file(str(file), language)
            report["repair_success"] = bool(success)

            if final["status"] == "OK":
                report["status"] = "REPAIRED"
            else:
                report["status"] = "REPAIR_FAILED"

            report["final_status"] = final["status"]

        elif language == "JavaScript":
            result = repair_javascript(str(file))

            report["repair_success"] = (
                result["status"] == "REPAIRED"
            )

            report["final_status"] = result["status"]

            if result["status"] == "REPAIRED":
                report["status"] = "REPAIRED"
            elif result["status"] == "ALREADY_VALID":
                report["status"] = "ALREADY_CLEAN"
            elif result["status"] == "UNSUPPORTED_ERROR":
                report["status"] = "MANUAL_REVIEW_REQUIRED"
            else:
                report["status"] = "REPAIR_FAILED"

            if result.get("backup"):
                report["backup"] = result["backup"]

        elif language == "PHP":
            original = file.read_text(encoding="utf-8")
            result = repair_php(original)

            if result["success"]:
                file.write_text(result["fixed_code"], encoding="utf-8")
                final = inspect_file(str(file), language)

                if final["status"] == "OK":
                    report["status"] = "REPAIRED"
                    report["repair_success"] = True
                    report["final_status"] = "OK"
                    report["changes"] = result["changes"]
                else:
                    file.write_text(original, encoding="utf-8")
                    report["status"] = "REPAIR_FAILED"
                    report["repair_success"] = False
                    report["final_status"] = final["status"]
            else:
                report["status"] = "MANUAL_REVIEW_REQUIRED"
                report["final_status"] = "ERROR"

        else:
            report["status"] = "MANUAL_REVIEW_REQUIRED"
            report["final_status"] = "ERROR"

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
