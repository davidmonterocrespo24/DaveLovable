"""
Utility modules for the application
"""

from .file_utils import (
    process_single_file_content,
    read_file_with_encoding,
    is_binary_file,
    detect_file_type,
    file_exists,
)

from .linter import lint_code_check

__all__ = [
    # file_utils
    "process_single_file_content",
    "read_file_with_encoding",
    "is_binary_file",
    "detect_file_type",
    "file_exists",
    # linter
    "lint_code_check",
]
