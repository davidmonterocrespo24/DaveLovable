"""
GREP Search Tool (Git Grep + Python Fallback)
"""

import re
import shutil
import subprocess
from pathlib import Path

from app.agents.tools.common import EXCLUDED_DIRS, get_workspace

EXCLUDED_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".obj",
    ".o",
    ".min.js",
    ".min.css",
    ".map",
    ".lock",
    ".log",
    ".sqlite",
    ".db",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".ico",
    ".pdf",
    ".woff",
    ".ttf",
}


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _run_git_grep(query: str, path: Path, include: str | None = None, case_sensitive: bool = False) -> str | None:
    """Executes optimized 'git grep'."""
    if not shutil.which("git"):
        return None

    cmd = ["git", "grep", "-n", "-I"]  # -n: line numbers, -I: ignore binary

    if not case_sensitive:
        cmd.append("-i")

    # Extended regex for better compatibility
    cmd.append("-E")

    # Build command
    # Note: git grep handles includes at the end with --
    cmd.append(query)

    if include:
        cmd.append("--")
        cmd.append(include)

    try:
        # Execute in target directory
        result = subprocess.run(cmd, cwd=str(path), capture_output=True, text=True, encoding="utf-8", errors="replace")

        if result.returncode == 0:
            return result.stdout
        elif result.returncode == 1:
            return ""  # No matches found
        else:
            return None  # Execution error (e.g. bad regex)

    except Exception:
        return None


def _python_grep_fallback(query: str, root_path: Path, include_pattern: str | None, case_sensitive: bool) -> str:
    """Pure Python implementation (slow but safe)."""
    results = []
    flags = 0 if case_sensitive else re.IGNORECASE

    try:
        pattern = re.compile(query, flags)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"

    # Collect files
    # If there's include_pattern, use glob with that pattern, otherwise rglob('*')
    search_pattern = include_pattern if include_pattern else "**/*"

    # Basic handling of relative glob if include doesn't have **
    if include_pattern and not include_pattern.startswith("**"):
        # If user requests "*.py", we want to search recursively "**/*.py"
        # This is a common UX heuristic for grep
        pass

    try:
        # Use rglob to iterate efficiently
        # Note: Path.rglob doesn't accept complex patterns like exclude, must filter manually
        files_iter = root_path.rglob(search_pattern) if include_pattern else root_path.rglob("*")

        for file_path in files_iter:
            if not file_path.is_file():
                continue

            # Exclusion filters
            if any(part in EXCLUDED_DIRS for part in file_path.parts):
                continue
            if file_path.suffix.lower() in EXCLUDED_EXTS:
                continue

            try:
                # Line-by-line reading to avoid loading large files into memory
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if pattern.search(line):
                            # Format compatible with git grep: file:line:content
                            # Truncate very long lines to avoid saturating context
                            clean_line = line.strip()[:300]
                            rel_path = file_path.relative_to(root_path)
                            results.append(f"{rel_path}:{i}:{clean_line}")

                            if len(results) >= 1000:  # Safety break
                                results.append("... (too many matches, truncated)")
                                return "\n".join(results)

            except Exception:
                continue

    except Exception as e:
        return f"Error in python grep: {e}"

    return "\n".join(results)


async def grep_search(
    query: str,
    case_sensitive: bool = False,
    include_pattern: str | None = None,
    exclude_pattern: str | None = None,  # Deprecated in favor of gitignore but kept for compat
    explanation: str | None = None,
) -> str:
    """
    Search for a regex pattern in files.
    """
    workspace = get_workspace()

    # 1. Try Git Grep (Fast Strategy)
    # Only if we're in a git repo and there are no complex exclusion patterns
    # (git grep uses .gitignore, which is usually what we want)
    if _is_git_repo(workspace) and not exclude_pattern:
        git_output = _run_git_grep(query, workspace, include_pattern, case_sensitive)
        if git_output is not None:
            if not git_output.strip():
                return f"No matches found for '{query}'"

            # Limit output if too long
            lines = git_output.splitlines()
            if len(lines) > 500:
                return "\n".join(lines[:500]) + f"\n... ({len(lines) - 500} more matches truncated)"
            return git_output

    # 2. Fallback to Python (Slow but Universal Strategy)
    # Used if git grep fails, if not a git repo, or if there are manual excludes
    return _python_grep_fallback(query, workspace, include_pattern, case_sensitive)
