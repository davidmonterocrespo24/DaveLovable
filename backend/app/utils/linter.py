import ast
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml


def _lint_python(content: str) -> str | None:
    try:
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"Python SyntaxError: {e.msg} at line {e.lineno}, column {e.offset}"


def _lint_json(content: str) -> str | None:
    try:
        json.loads(content)
        return None
    except json.JSONDecodeError as e:
        return f"JSON SyntaxError: {e.msg} at line {e.lineno}, column {e.colno}"


def _lint_yaml(content: str) -> str | None:
    try:
        yaml.safe_load(content)
        return None
    except yaml.YAMLError as e:
        return f"YAML SyntaxError: {e!s}"


def _lint_javascript(content: str) -> str | None:
    """
    Validates JS/TS using 'node --check'.
    Requires Node.js to be installed on the system.
    """
    if not shutil.which("node"):
        return None  # Node not installed, skip validation silently

    # Node requires a physical file for --check (stdin sometimes fails depending on version)
    try:
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Execute node --check
        result = subprocess.run(
            ["node", "--check", tmp_path],
            capture_output=True,
            text=True,
            timeout=5,  # Safety timeout
        )

        if result.returncode != 0:
            # Clean output to remove temp file path and make it readable
            error_msg = result.stderr.replace(tmp_path, "file.js").strip()
            # Take only first lines of error to avoid overwhelming the agent
            error_lines = "\n".join(error_msg.splitlines()[:5])
            return f"JavaScript SyntaxError:\n{error_lines}"

        return None

    except Exception:
        return None  # If subprocess fails, assume valid to not block
    finally:
        # Cleanup temporary file
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)


def _lint_bash(content: str) -> str | None:
    """Validates shell scripts using 'bash -n'"""
    if not shutil.which("bash"):
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = subprocess.run(["bash", "-n", tmp_path], capture_output=True, text=True, timeout=3)

        if result.returncode != 0:
            error_msg = result.stderr.replace(tmp_path, "script.sh").strip()
            return f"Bash SyntaxError: {error_msg}"
        return None
    except Exception:
        return None
    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)


# --- Main Dispatcher ---


def lint_code_check(file_path: str | Path, content: str) -> str | None:
    """
    Generic linting function.
    Returns a string with the error if validation fails, or None if it passes.
    """
    path_obj = Path(file_path)
    ext = path_obj.suffix.lower()

    # Map extensions to validators
    if ext == ".py":
        return _lint_python(content)

    elif ext == ".json":
        return _lint_json(content)

    elif ext in [".yaml", ".yml"]:
        return _lint_yaml(content)

    elif ext in [".js", ".mjs", ".cjs", ".ts", ".tsx"]:
        # Note: node --check works decently for basic TS too
        return _lint_javascript(content)

    elif ext in [".sh", ".bash"]:
        return _lint_bash(content)

    return None
