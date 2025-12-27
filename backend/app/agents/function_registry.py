"""
Function registry for AutoGen agents.
Defines functions that agents can call with proper schemas for AutoGen.
"""

from typing import Annotated, Literal
from app.agents.tools.file_operations import (
    read_file,
    write_file,
    edit_file,
    delete_file,
    list_dir,
)
from app.agents.tools.search_operations import (
    glob_search,
    grep_search,
    file_search,
)
from app.agents.tools.terminal_operations import (
    run_terminal_cmd,
)
from app.agents.tools.json_operations import (
    read_json,
    write_json,
)


# =============================================================================
# FUNCTION DEFINITIONS FOR AUTOGEN
# =============================================================================

def read_file_func(
    target_file: Annotated[str, "Path to the file to read"],
    should_read_entire_file: Annotated[bool, "Whether to read the entire file"] = True,
    start_line_one_indexed: Annotated[int, "Starting line number (1-indexed)"] = 1,
    end_line_one_indexed_inclusive: Annotated[int | None, "Ending line number (1-indexed, inclusive)"] = None,
) -> dict:
    """Read the contents of a file with support for reading specific line ranges."""
    return read_file(
        target_file=target_file,
        should_read_entire_file=should_read_entire_file,
        start_line_one_indexed=start_line_one_indexed,
        end_line_one_indexed_inclusive=end_line_one_indexed_inclusive,
    )


def write_file_func(
    target_file: Annotated[str, "Path to the file to write"],
    file_content: Annotated[str, "Content to write to the file"],
) -> dict:
    """Write content to a file. Creates the file if it doesn't exist."""
    return write_file(target_file=target_file, file_content=file_content)


def edit_file_func(
    target_file: Annotated[str, "Path to the file to modify"],
    old_string: Annotated[str, "Exact block of code to replace"],
    new_string: Annotated[str, "New block of code to insert"],
    instructions: Annotated[str, "Explanation of why this change is being made"] = "",
) -> dict:
    """Replace a specific block of text in a file using surgical search-and-replace."""
    return edit_file(
        target_file=target_file,
        old_string=old_string,
        new_string=new_string,
        instructions=instructions,
    )


def delete_file_func(
    target_file: Annotated[str, "Path to the file to delete"],
) -> dict:
    """Delete a file at the specified path."""
    return delete_file(target_file=target_file)


def list_dir_func(
    relative_workspace_path: Annotated[str, "Path to list contents of"] = ".",
) -> dict:
    """List the contents of a directory."""
    return list_dir(relative_workspace_path=relative_workspace_path)


def glob_search_func(
    pattern: Annotated[str, "Glob pattern to search (e.g., '**/*.py', 'src/**/*.ts')"],
    dir_path: Annotated[str | None, "Directory to search in (optional)"] = None,
    case_sensitive: Annotated[bool, "Whether search is case-sensitive"] = False,
) -> dict:
    """Search files by glob pattern."""
    return glob_search(
        pattern=pattern,
        dir_path=dir_path,
        case_sensitive=case_sensitive,
    )


def grep_search_func(
    query: Annotated[str, "Text or regex pattern to search for"],
    include_pattern: Annotated[str | None, "Glob pattern for files to include"] = None,
    exclude_pattern: Annotated[str | None, "Glob pattern for files to exclude"] = None,
    case_sensitive: Annotated[bool, "Whether the search should be case sensitive"] = False,
) -> dict:
    """Fast text-based search that finds exact pattern matches within files."""
    return grep_search(
        query=query,
        include_pattern=include_pattern,
        exclude_pattern=exclude_pattern,
        case_sensitive=case_sensitive,
    )


def file_search_func(
    query: Annotated[str, "Part of the filename or path to search for"],
) -> dict:
    """Fast fuzzy file search that matches against file paths."""
    return file_search(query=query)


def read_json_func(
    filepath: Annotated[str, "Path to the JSON file"],
    encoding: Annotated[str, "File encoding"] = "utf-8",
) -> dict:
    """Read and parse a JSON file."""
    return read_json(filepath=filepath, encoding=encoding)


def write_json_func(
    filepath: Annotated[str, "Path to the output JSON file"],
    data: Annotated[dict | list, "Data to write (dict or list)"],
    encoding: Annotated[str, "File encoding"] = "utf-8",
    indent: Annotated[int, "Indentation spaces"] = 2,
) -> dict:
    """Write data to a JSON file with proper formatting."""
    return write_json(
        filepath=filepath,
        data=data,
        encoding=encoding,
        indent=indent,
    )


# =============================================================================
# FUNCTION REGISTRY
# =============================================================================

FUNCTION_MAP = {
    "read_file": read_file_func,
    "write_file": write_file_func,
    "edit_file": edit_file_func,
    "delete_file": delete_file_func,
    "list_dir": list_dir_func,
    "glob_search": glob_search_func,
    "grep_search": grep_search_func,
    "file_search": file_search_func,
    "read_json": read_json_func,
    "write_json": write_json_func,
}


def get_function_map():
    """Get the function map for AutoGen agent registration."""
    return FUNCTION_MAP
