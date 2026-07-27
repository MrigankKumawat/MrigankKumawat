from pathlib import Path
import json
import os
from collections import Counter

ROOT = Path(os.environ.get("REPOS_DIR", "repos"))

EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".java": "Java",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".sql": "SQL",
}

IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "dist",
    "build",
}

counts = Counter()


def count_source_lines(text: str) -> int:
    """Count non-empty source lines."""
    return sum(1 for line in text.splitlines() if line.strip())


def process_notebook(path: Path) -> None:
    """
    Count code cells in Jupyter notebooks as Python.

    This assumes the notebooks on this profile are Python notebooks.
    """
    try:
        with path.open("r", encoding="utf-8") as file:
            notebook = json.load(file)

        for cell in notebook.get("cells", []):
            if cell.get("cell_type") != "code":
                continue

            source = cell.get("source", [])

            if isinstance(source, list):
                source = "".join(source)

            counts["Python"] += count_source_lines(source)

    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Skipping notebook {path}: {exc}")


def process_file(path: Path) -> None:
    if path.suffix.lower() == ".ipynb":
        process_notebook(path)
        return

    language = EXTENSIONS.get(path.suffix.lower())

    if not language:
        return

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        counts[language] += count_source_lines(text)

    except OSError as exc:
        print(f"Skipping {path}: {exc}")


def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    if should_ignore(path):
        continue

    process_file(path)


if not counts:
    raise SystemExit("No supported source files found.")


total = sum(counts.values())

languages = [
    (language, amount, amount / total * 100)
    for language, amount in counts.most_common(6)
]


COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#F1E05A",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "C++": "#F34B7D",
    "C": "#555555",
    "Java": "#B07219",
    "TypeScript": "#3178C6",
    "SQL": "#E38C00",
}


width = 400
height = 70 + len(languages) * 34

rows = []

for index, (language, amount, percentage) in enumerate(languages):
    y = 85 + index * 34
    color = COLORS.get(language, "#8B949E")

    rows.append(
        f'''
        <circle cx="28" cy="{y - 5}" r="5" fill="{color}" />

        <text
            x="42"
            y="{y}"
            fill="#C9D1D9"
            font-size="14"
            font-family="Segoe UI, Ubuntu, sans-serif"
        >
            {language}
        </text>

        <text
            x="365"
            y="{y}"
            fill="#2F81F7"
            font-size="14"
            text-anchor="end"
            font-family="Segoe UI, Ubuntu, sans-serif"
        >
            {percentage:.2f}%
        </text>
        '''
    )


svg = f'''
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
>

    <rect
        width="100%"
        height="100%"
        rx="8"
        fill="#1A1B27"
    />

    <text
        x="25"
        y="40"
        fill="#70A5FD"
        font-size="20"
        font-weight="600"
        font-family="Segoe UI, Ubuntu, sans-serif"
    >
        Most Used Languages
    </text>

    {''.join(rows)}

</svg>
'''


Path("top-langs.svg").write_text(svg, encoding="utf-8")

print("\nLanguage statistics:")

for language, amount, percentage in languages:
    print(f"{language}: {percentage:.2f}% ({amount} lines)")

print("\ntop-langs.svg generated successfully.")
