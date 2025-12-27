"""
Edit file tool for AutoGen agents.
Surgically edit specific text blocks in files.
"""

from typing import Dict, Any


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
