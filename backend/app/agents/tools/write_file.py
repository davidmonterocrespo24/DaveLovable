from pathlib import Path

from app.agents.tools.common import get_workspace
from app.utils.linter import lint_code_check


async def write_file(target_file: str, file_content: str) -> str:
    """
    Writes content to a file.

    IMPORTANT: This function AUTOMATICALLY creates all parent directories
    (like 'mkdir -p'). You do NOT need to create folders before calling this.

    Example: write_file('src/components/ui/Button.tsx', content) will
    automatically create 'src/', 'src/components/', and 'src/components/ui/'.
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

These files are for internal agent memory only and must not be written to the project."""

        workspace = get_workspace()
        target = workspace / target_file if not Path(target_file).is_absolute() else Path(target_file)
        # AUTOMATICALLY create all parent directories (like mkdir -p)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Syntax Guardrail
        lint_error = lint_code_check(target, file_content)
        if lint_error:
            return f"Error: The content you are trying to write has a syntax error.\n{lint_error}\nPlease fix the syntax before writing."

        # --- SANITY CHECK: PREVENT OVERWRITE DEMOLITION ---
        if target.exists():
            try:
                with open(target, encoding="utf-8") as f:
                    old_content = f.read()
                old_lines = len(old_content.splitlines())
                new_lines = len(file_content.splitlines())

                # Rule: If overwriting a large file (>1000 lines) with a small one (<100 lines)
                # Updated for Gemini-3 Flash: can handle much larger files
                if old_lines > 1000 and new_lines < 100:
                    return f"Error: You are trying to overwrite a large file ({old_lines} lines) with very little content ({new_lines} lines). This looks like accidental data loss. If you meant to edit the file, use 'edit_file' instead. If you actually want to replace the file, delete it first using 'delete_file' and then write it."
            except Exception:
                # If we can't read the file (e.g. binary), skip check
                pass
        # --------------------------------------------------

        with open(target, "w", encoding="utf-8") as f:
            f.write(file_content)
        return f"Successfully wrote {len(file_content)} characters to {target}"
    except Exception as e:
        return f"Error writing file: {e!s}"
