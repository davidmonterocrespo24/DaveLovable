import os
from pathlib import Path

# =============================================================================
# Directory Exclusion Configuration
# =============================================================================
# Centralized configuration for which directories to exclude/hide in all tools

# Directories to EXCLUDE from searches (file_search, grep, glob)
# These directories are completely ignored during traversal
EXCLUDED_DIRS = {
    ".daveagent",  # Internal agent configuration and data
    ".git",  # Git repository metadata
    "node_modules",  # Node.js dependencies
    "__pycache__",  # Python bytecode cache
    ".venv",  # Python virtual environment
    "venv",  # Python virtual environment (alternative name)
    "env",  # Python virtual environment (alternative name)
    ".pytest_cache",  # Pytest cache
    ".mypy_cache",  # MyPy type checker cache
    ".tox",  # Tox testing environments
    "dist",  # Distribution/build artifacts
    "build",  # Build artifacts
    ".next",  # Next.js build output
    ".nuxt",  # Nuxt.js build output
    "coverage",  # Test coverage reports
    ".idea",  # JetBrains IDE settings
    ".vscode",  # VS Code settings
    ".history",  # Local history (VS Code extension)
    ".agent_history",  # Agent history (VS Code extension)
}

# Directories to HIDE from directory listings (list_dir)
# These won't appear when listing directory contents
HIDDEN_DIRS = {
    ".daveagent",  # Internal agent configuration
    ".git",  # Git repository metadata
    ".agent_history",  # Agent history (VS Code extension)
    ".bandit",  # Bandit security scanner
}


def get_workspace():
    """Get current workspace dynamically - respects os.chdir() for evaluations"""
    return Path(os.getcwd()).resolve()
