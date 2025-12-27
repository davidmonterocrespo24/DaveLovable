"""
Glob search tool for AutoGen agents.
Search files by glob patterns.
"""

import os
import glob as glob_module
from typing import Dict, Optional, Any


def glob_search(
    pattern: str,
    dir_path: Optional[str] = None,
    case_sensitive: bool = False,
    explanation: str = ""
) -> Dict[str, Any]:
    """
    Search files by glob pattern.

    Args:
        pattern: Glob pattern to search (e.g., '**/*.py', 'src/**/*.ts')
        dir_path: Directory to search in (optional)
        case_sensitive: Whether search is case-sensitive
        explanation: Explanation for why this tool is being used

    Returns:
        Dictionary with matching file paths
    """
    try:
        search_path = dir_path if dir_path else "."
        full_pattern = os.path.join(search_path, pattern)
        matches = glob_module.glob(full_pattern, recursive=True)

        # Sort by modification time (most recent first)
        matches.sort(
            key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0,
            reverse=True
        )

        return {
            "success": True,
            "pattern": pattern,
            "search_path": search_path,
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
