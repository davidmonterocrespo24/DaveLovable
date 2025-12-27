"""
Read JSON tool for AutoGen agents.
Read and parse JSON files.
"""

import json
from typing import Dict, Any


def read_json(filepath: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Read and parse a JSON file.

    Args:
        filepath: Path to the JSON file
        encoding: File encoding (default: utf-8)

    Returns:
        Dictionary with parsed JSON data
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            data = json.load(f)

        return {
            "success": True,
            "data": data,
            "filepath": filepath,
            "type": type(data).__name__
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {filepath}"
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
