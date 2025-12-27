"""
Grep search tool for AutoGen agents.
Search for text/regex patterns within files.
"""

import os
import glob as glob_module
import re
from typing import Dict, Optional, Any, List


def grep_search(
    query: str,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
    case_sensitive: bool = False,
    explanation: str = ""
) -> Dict[str, Any]:
    """
    Fast text-based search that finds exact pattern matches within files.

    Args:
        query: Text or regex pattern to search for
        include_pattern: Glob pattern for files to include
        exclude_pattern: Glob pattern for files to exclude
        case_sensitive: Whether the search should be case sensitive
        explanation: Explanation for why this tool is being used

    Returns:
        Dictionary with search results
    """
    try:
        results: List[Dict[str, Any]] = []
        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            search_pattern = re.compile(query, flags)
        except re.error as e:
            return {
                "success": False,
                "error": f"Invalid regex pattern: {str(e)}"
            }

        # Get list of files to search
        if include_pattern:
            files = glob_module.glob(include_pattern, recursive=True)
        else:
            files = glob_module.glob("**/*", recursive=True)

        # Exclude patterns
        if exclude_pattern:
            exclude_files = set(glob_module.glob(exclude_pattern, recursive=True))
            files = [f for f in files if f not in exclude_files]

        # Common directories to exclude
        exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', 'out', 'coverage'
        }

        # Filter and search text files only
        for file_path in files:
            # Skip if in excluded directory
            if any(exc_dir in file_path.split(os.sep) for exc_dir in exclude_dirs):
                continue

            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if search_pattern.search(line):
                                results.append({
                                    "file": file_path,
                                    "line": line_num,
                                    "content": line.rstrip()
                                })
                                if len(results) >= 50:  # Limit results
                                    break
                except (UnicodeDecodeError, PermissionError, OSError):
                    # Skip binary files or files we can't read
                    continue

            if len(results) >= 50:
                break

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "truncated": len(results) >= 50
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
