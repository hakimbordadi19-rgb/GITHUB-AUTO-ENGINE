import os
import json

LANGUAGES = {
    ".py": "Python",
    ".php": "PHP",
    ".java": "Java",
    ".js": "JavaScript",
    ".c": "C",
    ".cpp": "C++",
    ".rs": "Rust",
    ".go": "Go"
}

def analyze(path):
    results = []

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in
                   [".git", "node_modules", ".venv", "build"]]

        for filename in files:
            ext = os.path.splitext(filename)[1]

            if ext in LANGUAGES:
                full = os.path.join(root, filename)

                results.append({
                    "file": full,
                    "language": LANGUAGES[ext],
                    "size": os.path.getsize(full)
                })

    return results

if __name__ == "__main__":
    data = analyze("projects")
    print(json.dumps(data, indent=2))
    print("Files analyzed:", len(data))
