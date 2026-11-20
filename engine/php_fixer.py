import re
import subprocess
import tempfile
import os


def inspect_php(source):
    try:
        result = subprocess.run(
            ["php", "-l"],
            input=source,
            text=True,
            capture_output=True,
            timeout=10
        )

        return {
            "valid": result.returncode == 0,
            "error": result.stderr or result.stdout
        }

    except Exception as error:
        return {
            "valid": False,
            "error": str(error)
        }


def repair_php(source):
    original = source
    changes = []

    patterns = [
        r'^\s*(?:echo|print|return)\s+.+(?<![;{}])$',
        r'^\s*\$[a-zA-Z_]\w*\s*=\s*.+(?<![;{}])$',
    ]

    lines = source.splitlines()
    repaired = []

    for line in lines:
        stripped = line.strip()

        if (
            stripped
            and not stripped.startswith(("//", "#", "*"))
            and not stripped.startswith(("<?php", "<?=", "/*"))
            and not stripped.endswith((";", "{", "}", ":"))
            and not stripped.startswith((
                "if ", "if(", "else", "elseif",
                "for ", "foreach ", "while ",
                "function ", "class ", "switch ",
                "try", "catch", "finally"
            ))
        ):
            for pattern in patterns:
                if re.match(pattern, line):
                    line += ";"
                    changes.append("Added missing semicolon")
                    break

        repaired.append(line)

    fixed_code = "\n".join(repaired)

    if fixed_code != original:
        check = inspect_php(fixed_code)

        if not check["valid"]:
            return {
                "success": False,
                "fixed_code": original,
                "changes": [],
                "error": check["error"]
            }

        return {
            "success": True,
            "fixed_code": fixed_code,
            "changes": changes,
            "error": None
        }

    return {
        "success": False,
        "fixed_code": original,
        "changes": [],
        "error": "No supported automatic repair found"
    }
