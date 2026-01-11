"""
File System Operations - Smart Edit v2 (With Auto-Correction)
"""

import os
import re
from pathlib import Path

from app.utils.linter import lint_code_check
from app.utils.llm_edit_fixer import _llm_fix_edit

# --- Helper Functions ---


def _normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n")


def _detect_line_ending(content: str) -> str:
    return "\r\n" if "\r\n" in content else "\n"


def _restore_line_endings(content: str, original_ending: str) -> str:
    if original_ending == "\n":
        return content
    return content.replace("\n", "\r\n")


# --- Replacement Strategies ---


def _calculate_exact_replacement(current_content: str, old_string: str, new_string: str):
    occurrences = current_content.count(old_string)
    if occurrences > 0:
        new_content = current_content.replace(old_string, new_string)
        return new_content, occurrences
    return None, 0


def _calculate_flexible_replacement(current_content: str, old_string: str, new_string: str):
    source_lines = current_content.splitlines(keepends=True)
    search_lines = old_string.splitlines()
    replace_lines = new_string.splitlines()
    search_lines_stripped = [line.strip() for line in search_lines if line.strip()]

    if not search_lines_stripped:
        return None, 0

    flexible_occurrences = 0
    new_source_lines = []
    i = 0

    while i < len(source_lines):
        potential_match = True
        search_idx = 0
        temp_idx = i

        while search_idx < len(search_lines_stripped) and temp_idx < len(source_lines):
            src_line = source_lines[temp_idx].strip()
            if not src_line:
                temp_idx += 1
                continue
            if src_line != search_lines_stripped[search_idx]:
                potential_match = False
                break
            search_idx += 1
            temp_idx += 1

        if potential_match and search_idx == len(search_lines_stripped):
            flexible_occurrences += 1
            first_line_match = source_lines[i]
            match = re.match(r"^(\s*)", first_line_match)
            indentation = match.group(1) if match else ""
            for r_line in replace_lines:
                new_source_lines.append(f"{indentation}{r_line}\n")
            i = temp_idx
        else:
            new_source_lines.append(source_lines[i])
            i += 1

    if flexible_occurrences > 0:
        return "".join(new_source_lines), flexible_occurrences
    return None, 0


def _calculate_regex_replacement(current_content: str, old_string: str, new_string: str):
    delimiters = [r"\(", r"\)", r":", r"\[", r"\]", r"\{", r"\}", r">", r"<", r"="]
    processed = old_string
    for d in delimiters:
        processed = re.sub(f"({d})", r" \1 ", processed)
    tokens = [t for t in processed.split() if t.strip()]

    if not tokens:
        return None, 0

    escaped_tokens = [re.escape(t) for t in tokens]
    pattern_str = r"\s*".join(escaped_tokens)
    final_pattern = f"(?m)^(\\s*){pattern_str}"

    try:
        regex = re.compile(final_pattern, re.DOTALL)
    except re.error:
        return None, 0

    match = regex.search(current_content)
    if not match:
        return None, 0

    indentation = match.group(1) or ""
    new_lines = new_string.splitlines()
    new_block = "\n".join([f"{indentation}{line}" for line in new_lines])

    new_content = current_content[: match.start()] + new_block + current_content[match.end() :]
    return new_content, 1


# --- Main Tool Function ---


async def edit_file(target_file: str, old_string: str, new_string: str, instructions: str = "") -> str:
    """
    Replaces a specific string in a file with a new string using smart matching strategies.

    This tool attempts to locate and replace text using the following strategies in order:
    1. Exact Match: strict literal string replacement.
    2. Flexible Match: ignores whitespace differences (indentation/newlines).
    3. Token-based Fuzzy Match: uses regex to match tokens regardless of formatting.
    4. LLM Auto-Correction: if enabled, asks an LLM to fix the search string based on the error.

    Args:
        target_file: Path to the file to be edited.
        old_string: The exact string to be replaced.
        new_string: The new string to replace the old string with.
        instructions: Optional description of the change (used for LLM auto-correction context).

    Returns:
        Success message with strategy used, or error message if replacement failed.
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

These files are for internal agent memory only and must not be edited in the project."""

        workspace = Path(os.getcwd()).resolve()
        target = workspace / target_file if not Path(target_file).is_absolute() else Path(target_file)

        if not target.exists():
            # Support creating new file if old_string is empty
            if not old_string:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(new_string)
                return f"Successfully created new file: {target_file}"
            return f"Error: File '{target_file}' not found."

        with open(target, encoding="utf-8") as f:
            raw_content = f.read()

        original_line_ending = _detect_line_ending(raw_content)
        current_content = _normalize_line_endings(raw_content)
        norm_old = _normalize_line_endings(old_string)
        norm_new = _normalize_line_endings(new_string)

        # Strategy Execution Loop
        strategies = [
            ("Exact Match", _calculate_exact_replacement),
            ("Flexible Match", _calculate_flexible_replacement),
            ("Token-based Fuzzy Match", _calculate_regex_replacement),
        ]

        new_content = None
        count = 0
        strategy_used = ""

        for name, strategy in strategies:
            res, cnt = strategy(current_content, norm_old, norm_new)
            if res and cnt > 0:
                new_content = res
                count = cnt
                strategy_used = name
                break

        # --- AUTO-CORRECTION ATTEMPT ---
        if count == 0:
            error_msg = "Could not find the 'old_string' using exact, flexible, or regex matching."

            # Intentar arreglar con LLM
            correction = await _llm_fix_edit(instructions, norm_old, norm_new, error_msg, current_content)

            if correction:
                fixed_old, fixed_new = correction
                # Reintentar solo Exact Match con los strings corregidos
                res, cnt = _calculate_exact_replacement(current_content, fixed_old, fixed_new)
                if res and cnt > 0:
                    new_content = res
                    count = cnt
                    strategy_used = "LLM Auto-Correction"

            if count == 0:  # Si aún falla
                return (
                    f"Error: {error_msg}\n"
                    f"1. Check exact indentation and whitespace.\n"
                    f"2. Use read_file to verify current content.\n"
                    f"3. Do NOT escape characters manually."
                )

        # --- GUARDRAILS ---
        # 1. Ensure we have content (should never be None at this point due to earlier checks)
        if new_content is None:
            return "Error: Failed to generate replacement content."

        # 2. No changes check
        if new_content == current_content:
            return "Error: The 'new_string' is identical to the found 'old_string'. No changes applied."

        # 3. Syntax Check (Modular Linter)
        lint_error = lint_code_check(str(target), new_content)
        if lint_error:
            return f"Error: Your edit caused a syntax error. Edit rejected.\n{lint_error}"

        # Save
        final_content = _restore_line_endings(new_content, original_line_ending)
        with open(target, "w", encoding="utf-8") as f:
            f.write(final_content)

        return f"Successfully edited {target_file} using {strategy_used} strategy. ({count} replacements)"

    except Exception as e:
        return f"System Error during edit: {e!s}"
