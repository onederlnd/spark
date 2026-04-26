import os

IGNORE = {
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "*.pyc",
    "*.pyo",
    "dist",
    "build",
    "*.egg-info",
    "uploads",
    "migrations",
    "NOTES-archive",
    "marketing",
}


def should_ignore(name):
    return name in IGNORE or name.endswith((".pyc", ".pyo"))


def tree(path, prefix=""):
    entries = sorted(
        [e for e in os.scandir(path) if not should_ignore(e.name)],
        key=lambda e: (not e.is_dir(), e.name.lower()),
    )
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(prefix + connector + entry.name)
        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            tree(entry.path, prefix + extension)


root = "."
print(root)
tree(root)
