"""
JSON operation tools for AutoGen agents.
Provides tools to read and write JSON files.
"""

import json
import os
from typing import Dict, Any, Union, List


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


def validate_json(filepath: str) -> Dict[str, Any]:
    """
    Validate that a file contains valid JSON.

    Args:
        filepath: Path to the JSON file to validate

    Returns:
        Dictionary with validation result
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)

        return {
            "success": True,
            "filepath": filepath,
            "message": "JSON is valid",
            "valid": True
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {filepath}",
            "valid": False
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}",
            "valid": False,
            "line": e.lineno,
            "column": e.colno
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "valid": False
        }
