from pathlib import Path

from app.agents.tools.common import get_workspace
from app.utils.file_utils import process_single_file_content


async def read_file(
    target_file: str,
    should_read_entire_file: bool = True,
    start_line_one_indexed: int = 1,
    end_line_one_indexed_inclusive: int = -1,
) -> str:
    """
    Read the contents of a file with line range support.
    Uses advanced file processing to handle large files, binary files, and different encodings.

    Args:
        target_file: Path to the file to be read
        should_read_entire_file: Whether to read the entire file or use line range
        start_line_one_indexed: Starting line number (1-based indexing)
        end_line_one_indexed_inclusive: Ending line number (1-based, inclusive). Use -1 for end of file.

    Returns:
        File contents with line range information, or error message if file not found
    """
    try:
        # GUARDRAIL: Block internal agent state files
        forbidden_files = [".agent_state.json", "agent_state.json"]
        if any(forbidden in target_file for forbidden in forbidden_files):
            return f"""🚨 FILE BLOCKED 🚨

File: {target_file}

This file is FORBIDDEN because it's an internal agent state file.
Agent state files should never be part of the user's project.

BLOCKED FILES:
• .agent_state.json
• agent_state.json

These files are for internal agent memory only and must not be read from the project."""

        workspace = get_workspace()

        # Resolve path
        if Path(target_file).is_absolute():
            resolved_path = Path(target_file)
        else:
            resolved_path = workspace / target_file

        str_path = str(resolved_path)
        str_workspace = str(workspace)

        # Calculate offset and limit
        offset = 0
        limit = None

        if not should_read_entire_file:
            offset = max(0, start_line_one_indexed - 1)
            if end_line_one_indexed_inclusive != -1:
                limit = end_line_one_indexed_inclusive - start_line_one_indexed + 1
                if limit < 0:
                    limit = 0

        # Call process_single_file_content
        result = await process_single_file_content(str_path, str_workspace, offset=offset, limit=limit)

        # Handle Error
        if result.get("error"):
            return f"Error: {result['error']}"

        # Handle Binary/Image content
        llm_content = result.get("llmContent")
        if not isinstance(llm_content, str):
            return_display = result.get("returnDisplay", "Binary or Media file")
            return f"[Media File Content]\n{return_display}\n(Content cannot be displayed as text)"

        # Handle Truncation
        if result.get("isTruncated"):
            lines_shown = result.get("linesShown", [0, 0])
            start_shown = lines_shown[0]
            end_shown = lines_shown[1]
            total_lines = result.get("originalLineCount", 0)

            next_start_line = end_shown + 1

            header = (
                f"IMPORTANT: The file content has been truncated.\n"
                f"Status: Showing lines {start_shown}-{end_shown} of {total_lines} total lines.\n"
                f"Action: To read more of the file, you can use the 'start_line_one_indexed' parameter in a subsequent 'read_file' call. "
                f"For example, to read the next section of the file, use start_line_one_indexed={next_start_line}.\n\n"
                f"--- FILE CONTENT (truncated) ---\n"
            )
            return header + llm_content

        # Normal Text Content
        header = f"File: {target_file}"
        if not should_read_entire_file:
            end_desc = end_line_one_indexed_inclusive if end_line_one_indexed_inclusive != -1 else "end"
            header += f" (lines {start_line_one_indexed}-{end_desc})"
        header += "\n"

        return header + llm_content

    except Exception as e:
        return f"Error reading file: {e!s}"
