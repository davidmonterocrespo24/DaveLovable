"""
Tools for AutoGen agents to interact with the project files and system.
These tools allow agents to read, write, search, and manipulate files.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import glob as glob_module
import re


# =============================================================================
# FILE OPERATIONS
# =============================================================================

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
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
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
            return {"success": True, "file_path": target_file, "message": "File deleted"}
        else:
            return {"success": False, "error": f"File not found: {target_file}"}
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
            return {"success": False, "error": f"Directory not found: {relative_workspace_path}"}

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


# =============================================================================
# SEARCH OPERATIONS
# =============================================================================

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
        matches = glob_module.glob(f"{search_path}/{pattern}", recursive=True)

        return {
            "success": True,
            "pattern": pattern,
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


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
        results = []
        search_pattern = re.compile(query, 0 if case_sensitive else re.IGNORECASE)

        # Get list of files to search
        if include_pattern:
            files = glob_module.glob(include_pattern, recursive=True)
        else:
            files = glob_module.glob("**/*", recursive=True)

        # Filter text files only
        for file_path in files:
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
                except (UnicodeDecodeError, PermissionError):
                    continue

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


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
        matches = []
        query_lower = query.lower()

        for file_path in glob_module.glob("**/*", recursive=True):
            if query_lower in file_path.lower():
                matches.append(file_path)
                if len(matches) >= 10:  # Limit results
                    break

        return {
            "success": True,
            "query": query,
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# TERMINAL OPERATIONS
# =============================================================================

def run_terminal_cmd(
    command: str,
    explanation: str = "",
    is_background: bool = False,
    require_user_approval: bool = True
) -> Dict[str, Any]:
    """
    Run a terminal command.

    Args:
        command: The terminal command to execute
        explanation: Explanation for why this command needs to be run
        is_background: Whether the command should be run in the background
        require_user_approval: Whether user must approve before execution

    Returns:
        Dictionary with command output
    """
    try:
        if require_user_approval:
            return {
                "success": False,
                "error": "User approval required for this command",
                "command": command,
                "requires_approval": True
            }

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out after 30 seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# JSON OPERATIONS
# =============================================================================

def read_json(filepath: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """Read and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            data = json.load(f)
        return {"success": True, "data": data, "filepath": filepath}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_json(
    filepath: str,
    data: Any,
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False
) -> Dict[str, Any]:
    """Write data to a JSON file with proper formatting."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        return {"success": True, "filepath": filepath}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# TOOL REGISTRY
# =============================================================================

TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "delete_file": delete_file,
    "list_dir": list_dir,
    "glob_search": glob_search,
    "grep_search": grep_search,
    "file_search": file_search,
    "run_terminal_cmd": run_terminal_cmd,
    "read_json": read_json,
    "write_json": write_json,
}


def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Execute a tool by name with the given arguments.

    Args:
        tool_name: Name of the tool to execute
        **kwargs: Arguments to pass to the tool

    Returns:
        Dictionary with tool execution results
    """
    if tool_name not in TOOLS:
        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found. Available tools: {list(TOOLS.keys())}"
        }

    try:
        tool_func = TOOLS[tool_name]
        result = tool_func(**kwargs)
        return result
    except TypeError as e:
        return {
            "success": False,
            "error": f"Invalid arguments for tool '{tool_name}': {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error executing tool '{tool_name}': {str(e)}"
        }
