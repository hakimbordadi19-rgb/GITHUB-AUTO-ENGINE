import shutil
import subprocess

TOOLS = {
    "Python": ["python", "--version"],
    "Java": ["javac", "-version"],
    "C/C++": ["clang", "--version"],
    "JavaScript": ["node", "--version"],
    "Go": ["go", "version"],
    "Rust": ["rustc", "--version"],
}


def check_tools():
    results = {}

    for language, command in TOOLS.items():
        executable = command[0]

        if not shutil.which(executable):
            print(f"[MISSING] {language}: compiler not installed")
            results[language] = False
            continue

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
            )

            output = result.stdout or result.stderr

            if result.returncode == 0:
                version = output.strip().splitlines()
                version = version[0] if version else "Version unknown"
                print(f"[AVAILABLE] {language}: {version}")
                results[language] = True
            else:
                print(f"[ERROR] {language}: {output[:500]}")
                results[language] = False

        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {language}")
            results[language] = False

        except OSError as error:
            print(f"[ERROR] {language}: {error}")
            results[language] = False

    return results


def main():
    check_tools()


if __name__ == "__main__":
    main()
