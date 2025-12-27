import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from app.core.config import settings


class GitService:
    """Service for Git version control operations"""

    @staticmethod
    def init_repository(project_id: int) -> bool:
        """
        Initialize a Git repository for a project
        Returns True if successful, False otherwise
        """
        from app.services.filesystem_service import FileSystemService

        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists():
            return False

        try:
            # Initialize git repository
            subprocess.run(
                ["git", "init"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            # Create .gitignore
            gitignore_content = """node_modules/
dist/
build/
.DS_Store
*.log
.env
.env.local
"""
            (project_dir / ".gitignore").write_text(gitignore_content)

            # Configure git user (for commits)
            subprocess.run(
                ["git", "config", "user.name", "Lovable AI"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "ai@lovable.dev"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            # Initial commit
            subprocess.run(
                ["git", "add", "."],
                cwd=project_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial commit: Project scaffolding"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            return True
        except subprocess.CalledProcessError as e:
            print(f"Git init failed: {e}")
            return False

    @staticmethod
    def commit_changes(project_id: int, message: str, files: Optional[List[str]] = None) -> bool:
        """
        Commit changes to the Git repository

        Args:
            project_id: The project ID
            message: Commit message
            files: Optional list of specific files to commit. If None, commits all changes.

        Returns:
            True if successful, False otherwise
        """
        from app.services.filesystem_service import FileSystemService

        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists() or not (project_dir / ".git").exists():
            return False

        try:
            # Add files
            if files:
                for file in files:
                    subprocess.run(
                        ["git", "add", file],
                        cwd=project_dir,
                        check=True,
                        capture_output=True
                    )
            else:
                subprocess.run(
                    ["git", "add", "."],
                    cwd=project_dir,
                    check=True,
                    capture_output=True
                )

            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=project_dir,
                capture_output=True
            )

            # If exit code is 1, there are changes to commit
            if result.returncode == 1:
                subprocess.run(
                    ["git", "commit", "-m", message],
                    cwd=project_dir,
                    check=True,
                    capture_output=True
                )
                return True

            # No changes to commit
            return True

        except subprocess.CalledProcessError as e:
            print(f"Git commit failed: {e}")
            return False

    @staticmethod
    def get_commit_history(project_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get commit history for a project

        Returns a list of commits with hash, author, date, and message
        """
        from app.services.filesystem_service import FileSystemService

        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists() or not (project_dir / ".git").exists():
            return []

        try:
            # Get commit log
            result = subprocess.run(
                [
                    "git", "log",
                    f"-{limit}",
                    "--pretty=format:%H|%an|%ad|%s",
                    "--date=iso"
                ],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    hash, author, date, message = line.split('|', 3)
                    commits.append({
                        "hash": hash,
                        "author": author,
                        "date": date,
                        "message": message
                    })

            return commits

        except subprocess.CalledProcessError as e:
            print(f"Git log failed: {e}")
            return []

    @staticmethod
    def get_file_at_commit(project_id: int, filepath: str, commit_hash: str) -> Optional[str]:
        """
        Get file content at a specific commit

        Returns the file content or None if not found
        """
        from app.services.filesystem_service import FileSystemService

        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists() or not (project_dir / ".git").exists():
            return None

        try:
            result = subprocess.run(
                ["git", "show", f"{commit_hash}:{filepath}"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )

            return result.stdout

        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def get_diff(project_id: int, filepath: Optional[str] = None) -> str:
        """
        Get diff of uncommitted changes

        Args:
            project_id: The project ID
            filepath: Optional specific file to diff. If None, shows all changes.

        Returns:
            Diff output as string
        """
        from app.services.filesystem_service import FileSystemService

        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists() or not (project_dir / ".git").exists():
            return ""

        try:
            cmd = ["git", "diff"]
            if filepath:
                cmd.append(filepath)

            result = subprocess.run(
                cmd,
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )

            return result.stdout

        except subprocess.CalledProcessError:
            return ""

    @staticmethod
    def restore_commit(project_id: int, commit_hash: str) -> bool:
        """
        Restore project to a specific commit (creates a new commit)

        Returns True if successful, False otherwise
        """
        from app.services.filesystem_service import FileSystemService

        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists() or not (project_dir / ".git").exists():
            return False

        try:
            # Revert to the commit (creates a new commit)
            subprocess.run(
                ["git", "revert", "--no-commit", commit_hash],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            subprocess.run(
                ["git", "commit", "-m", f"Restore to commit {commit_hash[:7]}"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            return True

        except subprocess.CalledProcessError as e:
            print(f"Git restore failed: {e}")
            return False
