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
def project_statistics(path):
    results = analyze(path)

    total_files = len(results)
    total_size = sum(item["size"] for item in results)

    languages = {}
    extensions = {}

    for item in results:
        language = item["language"]
        languages[language] = languages.get(language, 0) + 1

        extension = os.path.splitext(item["file"])[1]
        extensions[extension] = extensions.get(extension, 0) + 1

    average_size = total_size / total_files if total_files else 0

    return {
        "total_files": total_files,
        "total_size": total_size,
        "average_size": average_size,
        "languages": languages,
        "extensions": extensions
    }


if __name__ == "__main__":
    data = analyze("projects")
    print(json.dumps(data, indent=2))
    print("Files analyzed:", len(data))
