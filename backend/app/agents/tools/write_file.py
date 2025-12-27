"""
Write file tool for AutoGen agents.
Create or overwrite files with content.
"""

import os
from typing import Dict, Any


def write_file(target_file: str, file_content: str) -> Dict[str, Any]:
    """
    Write content to a file. Creates the file if it doesn't exist.

    Args:
        target_file: Path to the file to write
        file_content: Content to write to the file

    Returns:
        Dictionary with success status
    """
    try:
        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(target_file)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(file_content)

        return {
            "success": True,
            "file_path": target_file,
            "bytes_written": len(file_content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
