"""
Terminal operation tools for AutoGen agents.
Provides tools to execute terminal commands.
"""

import subprocess
from typing import Dict, Any


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
        # Security check - require approval for sensitive commands
        if require_user_approval:
            return {
                "success": False,
                "error": "User approval required for this command",
                "command": command,
                "requires_approval": True,
                "message": "This command requires user approval before execution"
            }

        # Execute the command
        if is_background:
            # Start process in background
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return {
                "success": True,
                "command": command,
                "message": f"Command started in background with PID: {process.pid}",
                "pid": process.pid,
                "background": True
            }
        else:
            # Run and wait for completion
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
        return {
            "success": False,
            "error": "Command timed out after 30 seconds",
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command
        }
