"""
Tool for executing terminal commands safely
"""

import subprocess
import os

from app.agents.tools.common import get_workspace


async def run_terminal_cmd(
    command: str,
    is_background: bool = False,
    require_user_approval: bool = False,
    explanation: str = "",
) -> str:
    """Executes a terminal command"""
    try:
        workspace = get_workspace()
        # shell=True is required for terminal command execution tool
        result = subprocess.run(  # nosec B602
            command, shell=True, capture_output=True, text=True, timeout=60, cwd=workspace
        )

        output = f"Command: {command}\n"
        output += f"Exit code: {result.returncode}\n\n"

        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"

        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"

        return output

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"
