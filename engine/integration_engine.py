import json
import sys
from pathlib import Path

from engine.analyzer import LANGUAGES
from engine.intelligent_repair import intelligent_repair


EXCLUDED = {
    ".git", ".venv", "__pycache__",
    "node_modules", "build", ".pytest_cache"
}


def run_project(target):
    path = Path(target)

    report = {
        "target": str(path),
        "engine": "GITHUB-AUTO-ENGINE",
        "files_scanned": 0,
        "files_ignored": 0,
        "repaired": 0,
        "failed": 0,
        "manual_review": 0,
        "languages": {},
        "results": []
    }

    if not path.exists():
        report["status"] = "NOT_FOUND"
        return report

    if path.is_file():
        if any(part in EXCLUDED for part in path.parts):
            candidates = []
        else:
            candidates = [path]
    else:
        candidates = [
            item for item in path.rglob("*")
            if item.is_file()
            and not any(part in EXCLUDED for part in item.parts)
        ]

    for file in candidates:
        language = LANGUAGES.get(file.suffix.lower())

        if not language:
            report["files_ignored"] += 1
            continue

        report["files_scanned"] += 1
        report["languages"][language] = (
            report["languages"].get(language, 0) + 1
        )

        result = intelligent_repair(str(file))
        report["results"].append(result)

        if result["status"] == "REPAIRED":
            report["repaired"] += 1
        elif result["status"] in ("REPAIR_FAILED", "EXCEPTION"):
            report["failed"] += 1
        elif result["status"] == "MANUAL_REVIEW_REQUIRED":
            report["manual_review"] += 1

    report["status"] = "COMPLETED"
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m engine.integration_engine PATH")
        raise SystemExit(2)

    print(json.dumps(
        run_project(sys.argv[1]),
        indent=4,
        ensure_ascii=False
    ))
