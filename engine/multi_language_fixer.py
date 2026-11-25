import re
import tempfile
from pathlib import Path

from engine.error_detector import inspect_file
from engine.safe_io import safe_replace, safe_restore


REPAIR_RULES = {
    "Java": (
        r'^(\s*System\.out\.println\("(?:\\.|[^"\\])*"\s*)$',
        r'\1);',
    ),
    "C": (
        r'^(\s*printf\("(?:\\.|[^"\\])*"\s*)$',
        r'\1);',
    ),
    "C++": (
        r'^(\s*std::cout\s*<<\s*"(?:\\.|[^"\\])*"\s*)$',
        r'\1;',
    ),
    "Go": (
        r'^(\s*fmt\.Println\("(?:\\.|[^"\\])*"\s*)$',
        r'\1)',
    ),
    "Rust": (
        r'^(\s*println!\("(?:\\.|[^"\\])*"\s*)$',
        r'\1);',
    ),
}


def repair_multilanguage(path, language):
    file = Path(path)

    report = {
        "file": str(file),
        "language": language,
        "status": "UNKNOWN",
        "backup": None,
        "error": None,
        "rollback_attempted": False,
        "rollback_success": None,
    }

    if not file.is_file():
        report["status"] = "NOT_FOUND"
        return report

    if language not in REPAIR_RULES:
        report["status"] = "UNSUPPORTED"
        return report

    initial = inspect_file(str(file), language)

    if initial["status"] == "OK":
        report["status"] = "ALREADY_CLEAN"
        return report

    if initial["status"] == "SKIPPED":
        report["status"] = "CHECKER_UNAVAILABLE"
        return report

    try:
        source = file.read_text(encoding="utf-8")
        lines = source.splitlines()

        pattern, replacement = REPAIR_RULES[language]
        changed = False

        for index, line in enumerate(lines):
            if re.fullmatch(pattern, line):
                lines[index] = re.sub(
                    pattern, replacement, line
                )
                changed = True
                break

        if not changed:
            report["status"] = "MANUAL_REVIEW_REQUIRED"
            return report

        candidate = "\n".join(lines)

        if source.endswith("\n"):
            candidate += "\n"

        with tempfile.TemporaryDirectory() as temp:
            candidate_path = Path(temp) / file.name
            candidate_path.write_text(
                candidate, encoding="utf-8"
            )

            validation = inspect_file(
                str(candidate_path), language
            )

        if validation["status"] != "OK":
            report["status"] = "VALIDATION_FAILED"
            report["error"] = validation["errors"]
            return report

        backup = safe_replace(
            file,
            candidate,
            backup_dir=file.parent / ".backups",
        )

        report["backup"] = str(backup)

        final = inspect_file(str(file), language)

        if final["status"] != "OK":
            report["rollback_attempted"] = True

            try:
                safe_restore(file, backup)
                report["rollback_success"] = True
                report["status"] = "REPAIR_FAILED"

            except Exception as error:
                report["rollback_success"] = False
                report["status"] = "ROLLBACK_FAILED"
                report["error"] = str(error)

            return report

        report["status"] = "REPAIRED"
        return report

    except Exception as error:
        report["status"] = "EXCEPTION"
        report["error"] = str(error)
        return report
