from pathlib import Path

from src.tools.common import get_workspace
from src.utils.linter import lint_code_check


async def write_file(target_file: str, file_content: str) -> str:
    """Writes content to a file"""
    try:
        workspace = get_workspace()
        target = (
            workspace / target_file if not Path(target_file).is_absolute() else Path(target_file)
        )
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

                # Rule: If overwriting a large file (>200 lines) with a small one (<50 lines)
                if old_lines > 200 and new_lines < 50:
                    return f"Error: You are trying to overwrite a large file ({old_lines} lines) with very little content ({new_lines} lines). This looks like accidental data loss. If you meant to edit the file, use 'edit_file' instead. If you actually want to replace the file, delete it first using 'delete_file' and then write it."
            except Exception:
                # If we can't read the file (e.g. binary), skip check
                pass
        # --------------------------------------------------

        with open(target, "w", encoding="utf-8") as f:
            f.write(file_content)
        return f"Successfully wrote {len(file_content)} characters to {target}"
    except Exception as e:
        return f"Error writing file: {str(e)}"
