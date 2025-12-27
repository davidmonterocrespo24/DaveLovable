"""
File search tool for AutoGen agents.
Fuzzy search for files by name.
"""

import os
import glob as glob_module
from typing import Dict, Any, List


def file_search(query: str, explanation: str = "") -> Dict[str, Any]:
    """
    Fast fuzzy file search that matches against file paths.

    Args:
        query: Part of the filename or path to search for
        explanation: Explanation for why this tool is being used

    Returns:
        Dictionary with matching file paths
    """
    try:
        matches: List[str] = []
        query_lower = query.lower()

        for file_path in glob_module.glob("**/*", recursive=True):
            if os.path.isfile(file_path):
                if query_lower in file_path.lower():
                    matches.append(file_path)
                    if len(matches) >= 10:  # Limit results
                        break

        return {
            "success": True,
            "query": query,
            "matches": matches,
            "count": len(matches),
            "truncated": len(matches) >= 10
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
