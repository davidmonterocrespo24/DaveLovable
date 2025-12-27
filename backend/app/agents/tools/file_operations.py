"""
File operation tools for AutoGen agents.
Provides tools to read, write, edit, delete, and list files.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any


def read_file(
    target_file: str,
    should_read_entire_file: bool = True,
    start_line_one_indexed: int = 1,
    end_line_one_indexed_inclusive: Optional[int] = None,
    explanation: str = ""
) -> Dict[str, Any]:
    """
    Read the contents of a file with support for reading specific line ranges.

    Args:
        target_file: Path to the file to read
        should_read_entire_file: Whether to read the entire file
        start_line_one_indexed: Starting line number (1-indexed)
        end_line_one_indexed_inclusive: Ending line number (1-indexed, inclusive)
        explanation: Explanation for why this tool is being used

    Returns:
        Dictionary with file contents and metadata
    """
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if should_read_entire_file:
            content = ''.join(lines)
            num_lines = len(lines)
        else:
            start_idx = start_line_one_indexed - 1
            end_idx = end_line_one_indexed_inclusive if end_line_one_indexed_inclusive else len(lines)
            selected_lines = lines[start_idx:end_idx]
            content = ''.join(selected_lines)
            num_lines = len(selected_lines)

        return {
            "success": True,
            "content": content,
            "file_path": target_file,
            "num_lines": num_lines,
            "total_lines": len(lines)
        }
    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {target_file}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


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


def edit_file(
    target_file: str,
    old_string: str,
    new_string: str,
    instructions: str = ""
) -> Dict[str, Any]:
    """
    Replace a specific block of text in a file using surgical search-and-replace.

    Args:
        target_file: Path to the file to modify
        old_string: Exact block of code to replace
        new_string: New block of code to insert
        instructions: Explanation of why this change is being made

    Returns:
        Dictionary with success status
    """
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_string not in content:
            return {
                "success": False,
                "error": f"String not found in file. Make sure old_string matches exactly."
            }

        # Replace only the first occurrence
        new_content = content.replace(old_string, new_string, 1)

        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return {
            "success": True,
            "file_path": target_file,
            "changes_made": instructions or "Text replaced"
        }
    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {target_file}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


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

        items = []
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
