from pathlib import Path

from engine.analyzer import LANGUAGES
from engine.error_detector import inspect_file
from engine.auto_fixer import repair
from engine.javascript_fixer import repair_javascript
from engine.php_fixer import repair_php
from engine.safe_io import safe_replace, safe_restore


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
        # Python repair
        if language == "Python":
            success = repair(str(file))
            final = inspect_file(str(file), language)

            report["repair_success"] = (
                bool(success) and final["status"] == "OK"
            )
            report["final_status"] = final["status"]

            if final["status"] == "OK":
                report["status"] = "REPAIRED"
            else:
                report["status"] = "REPAIR_FAILED"

        # JavaScript repair
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

        # PHP repair
        elif language == "PHP":
            original = file.read_text(encoding="utf-8")
            result = repair_php(original)

            if not result.get("success"):
                report["status"] = "MANUAL_REVIEW_REQUIRED"
                report["final_status"] = "ERROR"

            else:
                backup_path = None

                try:
                    backup_path = safe_replace(
                        file,
                        result["fixed_code"],
                        backup_dir=file.parent / ".backups"
                    )

                    final = inspect_file(str(file), language)

                    if final["status"] == "OK":
                        report["status"] = "REPAIRED"
                        report["repair_success"] = True
                        report["final_status"] = "OK"
                        report["changes"] = result["changes"]
                        report["backup"] = backup_path

                    else:
                        safe_restore(file, backup_path)
                        backup_path = None

                        report["status"] = "REPAIR_FAILED"
                        report["repair_success"] = False
                        report["final_status"] = final["status"]

                except Exception:
                    if backup_path is not None:
                        safe_restore(file, backup_path)
                    raise

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
