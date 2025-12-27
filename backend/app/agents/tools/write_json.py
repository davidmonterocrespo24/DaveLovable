"""
Write JSON tool for AutoGen agents.
Write data to JSON files with formatting.
"""

import json
import os
from typing import Dict, Any, Union, List


def write_json(
    filepath: str,
    data: Union[Dict, List],
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False
) -> Dict[str, Any]:
    """
    Write data to a JSON file with proper formatting.

    Args:
        filepath: Path to the output JSON file
        data: Data to write (dict or list)
        encoding: File encoding (default: utf-8)
        indent: Indentation spaces (default: 2)
        ensure_ascii: Escape non-ASCII characters (default: false)

    Returns:
        Dictionary with success status
    """
    try:
        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(filepath)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

        return {
            "success": True,
            "filepath": filepath,
            "message": "JSON file written successfully"
        }
    except TypeError as e:
        return {
            "success": False,
            "error": f"Data is not JSON serializable: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
