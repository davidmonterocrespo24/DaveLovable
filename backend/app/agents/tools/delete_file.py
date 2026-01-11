import os


async def delete_file(target_file: str, explanation: str = "") -> str:
    """
    Delete a file at the specified path.

    Parameters:
        target_file (str): The path to the file to be deleted
        explanation (str): Optional explanation for the deletion operation

    Returns:
        str: Success message if file deleted, error message if not found or failed
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

These files are for internal agent memory only and must not be deleted from the project."""

        if os.path.exists(target_file):
            os.remove(target_file)
            return f"Successfully deleted file: {target_file}"
        else:
            return f"File not found: {target_file}"
    except Exception as e:
        return f"Error deleting file: {e!s}"
