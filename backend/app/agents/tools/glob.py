import glob
import logging
import os
import time
from pathlib import Path
from typing import Optional

from app.agents.tools.common import EXCLUDED_DIRS, get_workspace

# Configure logging
logger = logging.getLogger(__name__)

RECENCY_THRESHOLD_SECONDS = 24 * 60 * 60  # 24 hours
MAX_RESULTS_LIMIT = 200  # Safety limit for context window

# Optional import for pathspec
import pathspec

WORKSPACE = Path(os.getcwd()).resolve()


def _load_gitignore_patterns(root_path: Path) -> Optional["pathspec.PathSpec"]:
    gitignore = root_path / ".gitignore"
    if gitignore.exists():
        try:
            with open(gitignore, encoding="utf-8") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        except Exception:
            return None
    return None


def _is_ignored(path: Path, spec: Optional["pathspec.PathSpec"]) -> bool:
    # Check hardcoded exclusions from common configuration
    parts = path.parts
    if any(excluded_dir in parts for excluded_dir in EXCLUDED_DIRS):
        return True

    # Check gitignore patterns if available
    if spec:
        try:
            rel_path = path.relative_to(WORKSPACE)
            return spec.match_file(str(rel_path))
        except ValueError:
            return False
    return False


def _sort_file_entries(entries: list[Path]) -> list[Path]:
    now = time.time()

    def get_sort_key(path_obj: Path):
        try:
            stat = path_obj.stat()
            mtime = stat.st_mtime
        except Exception:
            mtime = 0

        is_recent = (now - mtime) < RECENCY_THRESHOLD_SECONDS

        # Sort key: (is_old_bool, neg_mtime_if_recent, path_str)
        if is_recent:
            return (0, -mtime, str(path_obj))
        else:
            return (1, 0, str(path_obj))

    return sorted(entries, key=get_sort_key)


async def glob_search(
    pattern: str,
    dir_path: str | None = None,
    case_sensitive: bool = False,
    respect_git_ignore: bool = True,
) -> str:
    """
    Efficiently finds files matching specific glob patterns.
    """
    try:
        workspace = get_workspace()

        # Determine search directory
        if dir_path:
            search_dir = Path(dir_path)
            if not search_dir.is_absolute():
                search_dir = (workspace / search_dir).resolve()
        else:
            search_dir = workspace

        # Security check: Ensure search dir is within workspace
        if not str(search_dir).startswith(str(workspace)):
            return f"Error: Search path '{dir_path}' is outside the workspace."

        if not search_dir.exists():
            return f"Error: Search path does not exist: {search_dir}"

        # Construct absolute pattern
        if Path(pattern).is_absolute():
            full_pattern = pattern
        else:
            full_pattern = str(search_dir / pattern)

        # Optimization: Load gitignore only once
        gitignore_spec = None
        if respect_git_ignore and (workspace / ".git").exists():
            gitignore_spec = _load_gitignore_patterns(workspace)

        # Execute glob
        # recursive=True allows '**' logic
        files = glob.glob(full_pattern, recursive=True)

        # Filter files and ignores
        path_entries = []
        for f in files:
            p = Path(f)
            if p.is_file():
                if respect_git_ignore and _is_ignored(p, gitignore_spec):
                    continue
                path_entries.append(p)

        if not path_entries:
            return f'No files found matching pattern "{pattern}" within {search_dir}'

        # Sort logic
        sorted_entries = _sort_file_entries(path_entries)

        # Truncate results if too many
        total_count = len(sorted_entries)
        if total_count > MAX_RESULTS_LIMIT:
            sorted_entries = sorted_entries[:MAX_RESULTS_LIMIT]
            truncated_msg = f"\n... ({total_count - MAX_RESULTS_LIMIT} more files truncated)"
        else:
            truncated_msg = ""

        # Format output: Use Relative Paths for clarity (less tokens)
        # If path is inside workspace, make relative. Else keep absolute.
        output_paths = []
        for p in sorted_entries:
            try:
                output_paths.append(str(p.relative_to(workspace)))
            except ValueError:
                output_paths.append(str(p))

        file_list = "\n".join(output_paths)

        return f'Found {total_count} file(s) matching "{pattern}" within {search_dir}, sorted by modification time (newest first):\n{file_list}{truncated_msg}'

    except Exception as e:
        return f"Error during glob search operation: {e!s}"
