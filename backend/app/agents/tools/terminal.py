"""
Tool for executing terminal commands safely
"""

import subprocess

from app.agents.tools.common import get_workspace


async def run_terminal_cmd(
    command: str,
    is_background: bool = False,
    explanation: str = "",
) -> str:
    """Executes a terminal command"""
    try:
        workspace = get_workspace()

        # GUARDRAIL: Block forbidden development server commands AND build commands
        # These commands won't work because Node.js runs in WebContainer (browser), not in this backend
        forbidden_patterns = [
            "npm run dev",
            "npm run build",
            "npm start",
            "yarn dev",
            "yarn build",
            "yarn start",
            "pnpm dev",
            "pnpm build",
            "pnpm start",
            "vite",
            "vite dev",
            "vite build",
            "vite preview",
            "tsc",
            "npx tsc",
            "react-scripts start",
            "react-scripts build",
            "next dev",
            "next build",
            "next start",
        ]

        command_lower = command.lower().strip()

        # Check for forbidden commands
        for forbidden in forbidden_patterns:
            if forbidden in command_lower:
                return f"""🚨 COMMAND BLOCKED 🚨

Command: {command}

This command is FORBIDDEN because Node.js commands cannot run in this backend environment.
The project runs in WebContainer (in the browser), not in this Python backend.

BLOCKED COMMANDS:
• npm run dev, npm run build, npm start
• yarn dev, yarn build, yarn start
• pnpm dev, pnpm build, pnpm start
• vite, vite dev, vite build, vite preview
• tsc, npx tsc --noEmit
• react-scripts start, react-scripts build
• next dev, next build, next start

WHY: These commands won't work because:
✗ Node.js project runs in WebContainer (browser), not in backend
✗ Backend is Python environment without Node.js in the project PATH
✗ Commands would fail with "command not found" or hang

WHAT YOU CAN DO INSTEAD:
✓ The preview panel shows your app running in WebContainer
✓ WebContainer automatically handles npm install, build, and dev server
✓ Changes are automatically hot-reloaded in the preview
✓ Use manual verification: list_dir + grep_search to check imports

VERIFICATION STRATEGY:
✓ Use list_dir("src/components") to verify files exist
✓ Use grep_search to find import statements and cross-check with created files
✓ WebContainer console shows TypeScript errors in real-time

The WebContainer environment handles all Node.js operations automatically."""

        # Check for background process attempts (commands with &)
        if "&" in command and not command.strip().endswith("&&"):
            return f"""🚨 BACKGROUND COMMAND BLOCKED 🚨

Command: {command}

Background commands (with &) are FORBIDDEN because they cause processes to hang indefinitely.

The WebContainer handles all server processes automatically."""

        # Fix common Unix commands for Windows compatibility
        import platform

        if platform.system() == "Windows":
            # Replace pwd with cd (shows current directory on Windows)
            if command.strip() == "pwd":
                command = "cd"
            # Replace ls with dir
            elif command.strip().startswith("ls"):
                command = command.replace("ls", "dir", 1)

        # Detect commands that might take a long time
        long_running_commands = [
            "tsc",
            "npx tsc",
            "npm audit",
            "npm outdated",
            "npm run build",
            "yarn build",
            "pnpm build",
        ]
        is_long_running = any(cmd in command_lower for cmd in long_running_commands)

        # Set timeout: 15 seconds for normal commands, 60 for build/check commands
        timeout_seconds = 60 if is_long_running else 15

        # shell=True is required for terminal command execution tool
        result = subprocess.run(  # nosec B602
            command, shell=True, capture_output=True, text=True, timeout=timeout_seconds, cwd=workspace
        )

        output = f"Command: {command}\n"
        output += f"Exit code: {result.returncode}\n\n"

        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"

        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"

        return output

    except subprocess.TimeoutExpired:
        return f"""⏱️ COMMAND TIMEOUT ⏱️

Command: {command}

This command took longer than {timeout_seconds} seconds and was automatically terminated.

REASON: Long-running commands are not suitable for this environment.

WHAT THIS MEANS:
• The command was processing for too long
• It may be checking too many files or doing complex analysis
• The WebContainer environment is better suited for development

ALTERNATIVES:
• For TypeScript checking: The editor already shows TypeScript errors in real-time
• For linting: Use specific file targets instead of the whole project
• For builds: The WebContainer handles builds automatically

The preview panel already provides real-time feedback on your code."""
    except Exception as e:
        return f"Error executing command: {e!s}"
