import shutil
import subprocess

TOOLS = {
    "Python": ["python", "--version"],
    "Java": ["javac", "-version"],
    "C/C++": ["clang", "--version"],
    "JavaScript": ["node", "--version"],
    "Go": ["go", "version"],
    "Rust": ["rustc", "--version"]
}

for language, command in TOOLS.items():
    executable = command[0]

    if shutil.which(executable):
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout or result.stderr
        print(f"[AVAILABLE] {language}: {output.strip().splitlines()[0]}")
    else:
        print(f"[MISSING] {language}: compiler not installed")
