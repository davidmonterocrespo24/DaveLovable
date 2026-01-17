"""
File utilities for reading and processing files.
Migrated from TypeScript implementation.
"""

import base64
import logging
import mimetypes
import os
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)

# Constants for text file processing
# Updated for Gemini-3 Flash: 1M input tokens allows reading much larger files
# Approximate: 1 token ≈ 4 characters, so 1M tokens ≈ 4M chars ≈ 100K lines of code
DEFAULT_MAX_LINES_TEXT_FILE = 50000  # Increased from 2000 to 50000 (25x more)
MAX_LINE_LENGTH_TEXT_FILE = 10000  # Increased from 2000 to 10000 (5x more) for long lines
DEFAULT_ENCODING = "utf-8"

# Binary extensions list (migrated from ignorePatterns.js concept)
BINARY_EXTENSIONS = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".obj",
    ".o",
    ".a",
    ".lib",
    ".iso",
    ".img",
    ".dmg",
    ".tar",
    ".gz",
    ".zip",
    ".7z",
    ".rar",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".ico",
    ".webp",
    ".mp3",
    ".wav",
    ".ogg",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".pyc",
    ".pyo",
    ".pyd",
    ".class",
    ".jar",
    ".war",
    ".ear",
}


class ToolErrorType:
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    TARGET_IS_DIRECTORY = "TARGET_IS_DIRECTORY"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    READ_CONTENT_FAILURE = "READ_CONTENT_FAILURE"


def detect_bom(buf: bytes) -> tuple[str, int] | None:
    """
    Detect a Unicode BOM (Byte Order Mark) if present.
    Returns (encoding, bom_length) or None.
    """
    if len(buf) >= 4:
        # UTF-32 LE: FF FE 00 00
        if buf[:4] == b"\xff\xfe\x00\x00":
            return ("utf-32-le", 4)
        # UTF-32 BE: 00 00 FE FF
        if buf[:4] == b"\x00\x00\xfe\xff":
            return ("utf-32-be", 4)

    if len(buf) >= 3:
        # UTF-8: EF BB BF
        if buf[:3] == b"\xef\xbb\xbf":
            return ("utf-8-sig", 3)  # Python handles BOM with utf-8-sig

    if len(buf) >= 2:
        # UTF-16 LE: FF FE
        if buf[:2] == b"\xff\xfe":
            return ("utf-16-le", 2)
        # UTF-16 BE: FE FF
        if buf[:2] == b"\xfe\xff":
            return ("utf-16-be", 2)

    return None


async def read_file_with_encoding(file_path: str) -> str:
    """
    Read a file as text, honoring BOM encodings.
    Falls back to utf-8 when no BOM is present.
    """
    try:
        with open(file_path, "rb") as f:
            full = f.read()

        if not full:
            return ""

        bom_info = detect_bom(full)

        if bom_info:
            encoding, _ = bom_info
            # Python's decode handles BOM stripping for utf-8-sig and utf-16
            # For utf-32, we might need to be careful, but standard codecs usually handle it.
            try:
                return full.decode(encoding)
            except UnicodeDecodeError:
                # Fallback if specific BOM decoding fails
                pass

        # Try UTF-8 first
        try:
            return full.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback to latin-1 or similar if utf-8 fails?
            # Or try to detect? For now, let's stick to utf-8 errors or try latin-1 as last resort
            return full.decode("latin-1")

    except Exception as e:
        raise OSError(f"Failed to read file {file_path}: {e!s}")


def get_specific_mime_type(file_path: str) -> str | None:
    """Looks up the specific MIME type for a file path."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type


def is_within_root(path_to_check: str, root_directory: str) -> bool:
    """Checks if a path is within a given root directory."""
    try:
        abs_check = os.path.abspath(path_to_check)
        abs_root = os.path.abspath(root_directory)
        return os.path.commonpath([abs_root, abs_check]) == abs_root
    except ValueError:
        return False


async def is_binary_file(file_path: str) -> bool:
    """
    Heuristic: determine if a file is likely binary.
    """
    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False

        # Sample up to 4KB
        sample_size = min(4096, os.path.getsize(file_path))
        with open(file_path, "rb") as f:
            buf = f.read(sample_size)

        if not buf:
            return False

        # Check for BOM
        if detect_bom(buf[:4]):
            return False

        # Check for null bytes and non-printable characters
        non_printable_count = 0
        for byte in buf:
            if byte == 0:
                return True
            if byte < 9 or (13 < byte < 32):
                non_printable_count += 1

        return (non_printable_count / len(buf)) > 0.3

    except Exception as e:
        logger.warning(f"Failed to check if file is binary: {file_path} - {e!s}")
        return False


async def detect_file_type(file_path: str) -> str:
    """
    Detects the type of file based on extension and content.
    Returns: 'text', 'image', 'pdf', 'audio', 'video', 'binary', 'svg'
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".ts", ".mts", ".cts", ".tsx"]:
        return "text"

    if ext == ".svg":
        return "svg"

    mime_type = get_specific_mime_type(file_path)
    if mime_type:
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("audio/"):
            return "audio"
        if mime_type.startswith("video/"):
            return "video"
        if mime_type == "application/pdf":
            return "pdf"

    if ext in BINARY_EXTENSIONS:
        return "binary"

    if await is_binary_file(file_path):
        return "binary"

    return "text"


async def process_single_file_content(
    file_path: str, root_directory: str, offset: int = 0, limit: int | None = None
) -> dict[str, Any]:
    """
    Reads and processes a single file, handling text, images, and PDFs.
    """
    try:
        if not os.path.exists(file_path):
            return {
                "llmContent": "Could not read file because no file was found at the specified path.",
                "returnDisplay": "File not found.",
                "error": f"File not found: {file_path}",
                "errorType": ToolErrorType.FILE_NOT_FOUND,
            }

        if os.path.isdir(file_path):
            return {
                "llmContent": "Could not read file because the provided path is a directory, not a file.",
                "returnDisplay": "Path is a directory.",
                "error": f"Path is a directory, not a file: {file_path}",
                "errorType": ToolErrorType.TARGET_IS_DIRECTORY,
            }

        # Updated for Gemini-3 Flash: 1M input tokens = ~4MB of text
        # Allow up to 50MB to support larger files (will be truncated by line limits)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50:
            return {
                "llmContent": "File size exceeds the 50MB limit.",
                "returnDisplay": "File size exceeds the 50MB limit.",
                "error": f"File size exceeds the 50MB limit: {file_path} ({file_size_mb:.2f}MB)",
                "errorType": ToolErrorType.FILE_TOO_LARGE,
            }

        file_type = await detect_file_type(file_path)
        relative_path = os.path.relpath(file_path, root_directory).replace("\\", "/")

        if file_type == "binary":
            return {
                "llmContent": f"Cannot display content of binary file: {relative_path}",
                "returnDisplay": f"Skipped binary file: {relative_path}",
            }

        elif file_type == "svg":
            if os.path.getsize(file_path) > 1 * 1024 * 1024:  # 1MB
                return {
                    "llmContent": f"Cannot display content of SVG file larger than 1MB: {relative_path}",
                    "returnDisplay": f"Skipped large SVG file (>1MB): {relative_path}",
                }
            content = await read_file_with_encoding(file_path)
            return {"llmContent": content, "returnDisplay": f"Read SVG as text: {relative_path}"}

        elif file_type == "text":
            content = await read_file_with_encoding(file_path)
            lines = content.splitlines()
            original_line_count = len(lines)

            start_line = offset
            effective_limit = limit if limit is not None else DEFAULT_MAX_LINES_TEXT_FILE
            end_line = min(start_line + effective_limit, original_line_count)
            actual_start_line = min(start_line, original_line_count)

            selected_lines = lines[actual_start_line:end_line]

            lines_truncated_in_length = False
            formatted_lines = []
            for line in selected_lines:
                if len(line) > MAX_LINE_LENGTH_TEXT_FILE:
                    lines_truncated_in_length = True
                    formatted_lines.append(line[:MAX_LINE_LENGTH_TEXT_FILE] + "... [truncated]")
                else:
                    formatted_lines.append(line)

            content_range_truncated = start_line > 0 or end_line < original_line_count
            is_truncated = content_range_truncated or lines_truncated_in_length
            llm_content = "\n".join(formatted_lines)

            return_display = ""
            if content_range_truncated:
                return_display = (
                    f"Read lines {actual_start_line + 1}-{end_line} of {original_line_count} from {relative_path}"
                )
                if lines_truncated_in_length:
                    return_display += " (some lines were shortened)"
            elif lines_truncated_in_length:
                return_display = (
                    f"Read all {original_line_count} lines from {relative_path} (some lines were shortened)"
                )

            return {
                "llmContent": llm_content,
                "returnDisplay": return_display,
                "isTruncated": is_truncated,
                "originalLineCount": original_line_count,
                "linesShown": [actual_start_line + 1, end_line],
            }

        elif file_type in ["image", "pdf", "audio", "video"]:
            with open(file_path, "rb") as f:
                content_buffer = f.read()
            base64_data = base64.b64encode(content_buffer).decode("utf-8")
            mime_type = get_specific_mime_type(file_path) or "application/octet-stream"

            return {
                "llmContent": {"inlineData": {"data": base64_data, "mimeType": mime_type}},
                "returnDisplay": f"Read {file_type} file: {relative_path}",
            }

        else:
            return {
                "llmContent": f"Unhandled file type: {file_type}",
                "returnDisplay": f"Skipped unhandled file type: {relative_path}",
                "error": f"Unhandled file type for {file_path}",
            }

    except Exception as e:
        error_message = str(e)
        display_path = os.path.relpath(file_path, root_directory).replace("\\", "/")
        return {
            "llmContent": f"Error reading file {display_path}: {error_message}",
            "returnDisplay": f"Error reading file {display_path}: {error_message}",
            "error": f"Error reading file {file_path}: {error_message}",
            "errorType": ToolErrorType.READ_CONTENT_FAILURE,
        }


async def file_exists(file_path: str) -> bool:
    return os.path.exists(file_path)
