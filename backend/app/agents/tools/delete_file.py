"""
Delete file tool for AutoGen agents.
Delete files from the filesystem.
"""

import os
from typing import Dict, Any


def delete_file(target_file: str, explanation: str = "") -> Dict[str, Any]:
    """
    Delete a file at the specified path.

    Args:
        target_file: Path to the file to delete
        explanation: Explanation for why this file is being deleted

    Returns:
        Dictionary with success status
    """
    try:
        if os.path.exists(target_file):
            os.remove(target_file)
            return {
                "success": True,
                "file_path": target_file,
                "message": "File deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": f"File not found: {target_file}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
