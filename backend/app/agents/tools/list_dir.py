"""
List directory tool for AutoGen agents.
List contents of directories.
"""

from pathlib import Path
from typing import Dict, Any, List


def list_dir(relative_workspace_path: str = ".", explanation: str = "") -> Dict[str, Any]:
    """
    List the contents of a directory.

    Args:
        relative_workspace_path: Path to list contents of
        explanation: Explanation for why this tool is being used

    Returns:
        Dictionary with directory contents
    """
    try:
        path = Path(relative_workspace_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {relative_workspace_path}"
            }

        if not path.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {relative_workspace_path}"
            }

        items: List[Dict[str, str]] = []
        for item in sorted(path.iterdir()):
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item)
            })

        return {
            "success": True,
            "path": relative_workspace_path,
            "items": items,
            "count": len(items)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
