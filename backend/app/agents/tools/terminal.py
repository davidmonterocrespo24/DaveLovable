"""
Tool for executing terminal commands safely
"""

import subprocess
import os

from app.agents.tools.common import get_workspace


async def run_terminal_cmd(
    command: str,
    is_background: bool = False,
    explanation: str = "",
) -> str:
    """Executes a terminal command"""
    try:
        workspace = get_workspace()

        # GUARDRAIL: Block forbidden development server commands
        # These commands interfere with WebContainer's automatic dev server
        forbidden_patterns = [
            'npm run dev',
            'npm start',
            'npm run build',
            'yarn dev',
            'yarn start',
            'yarn build',
            'pnpm dev',
            'pnpm start',
            'pnpm build',
            'vite',
            'vite dev',
            'vite build',
            'react-scripts start',
            'next dev',
            'next start',
        ]

        command_lower = command.lower().strip()

        # Check for forbidden commands
        for forbidden in forbidden_patterns:
            if forbidden in command_lower:
                return f"""🚨 COMMAND BLOCKED 🚨

Command: {command}

This command is FORBIDDEN because the WebContainer preview environment automatically handles running the development server.

BLOCKED COMMANDS:
• npm run dev, npm start, npm run build
• yarn dev, yarn start, yarn build
• pnpm dev, pnpm start, pnpm build
• vite, vite dev, vite build
• react-scripts start
• next dev, next start

WHY: Running these commands will:
✗ Cause the process to hang indefinitely
✗ Interfere with WebContainer's automatic server
✗ Waste time and resources

WHAT YOU CAN DO INSTEAD:
✓ The preview panel already shows your app running
✓ Changes are automatically hot-reloaded
✓ Just edit files and see changes instantly

ALLOWED COMMANDS:
✓ npm install <package> - Install dependencies
✓ npm ci - Clean install

If you need to test the application, it's already running in the WebContainer preview panel on the right side of the screen."""

        # Check for background process attempts (commands with &)
        if '&' in command and not command.strip().endswith('&&'):
            return f"""🚨 BACKGROUND COMMAND BLOCKED 🚨

Command: {command}

Background commands (with &) are FORBIDDEN because they cause processes to hang indefinitely.

The WebContainer handles all server processes automatically."""

        # Fix common Unix commands for Windows compatibility
        import platform
        if platform.system() == 'Windows':
            # Replace pwd with cd (shows current directory on Windows)
            if command.strip() == 'pwd':
                command = 'cd'
            # Replace ls with dir
            elif command.strip().startswith('ls'):
                command = command.replace('ls', 'dir', 1)

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
