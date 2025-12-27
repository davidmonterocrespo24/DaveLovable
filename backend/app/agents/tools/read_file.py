"""
Read file tool for AutoGen agents.
Read the contents of files with line range support.
"""

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
