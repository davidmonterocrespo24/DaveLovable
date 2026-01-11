"""
Git Tools for AutoGen - Basic git operations
"""

import asyncio
import os


async def git_status(path: str | None = None) -> str:
    """
    Gets the git repository status.

    Args:
        path: Repository path (uses current directory if not specified)

    Returns:
        str: Repository status in readable format
    """
    work_dir = path or os.getcwd()

    try:
        # Verify if it's a git repository
        proc = await asyncio.create_subprocess_exec(
            "git",
            "rev-parse",
            "--git-dir",
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {work_dir} is not a git repository"

        # Get status
        proc = await asyncio.create_subprocess_exec(
            "git",
            "status",
            "--porcelain=v1",
            "-b",
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode("utf-8", errors="replace")
        lines = output.strip().split("\n") if output.strip() else []

        # Parse information
        branch_line = lines[0] if lines else ""
        branch = branch_line[3:].split("...")[0] if branch_line.startswith("##") else "unknown"

        # Count files by status
        staged = sum(1 for line in lines[1:] if line and line[0] in "MADRC")
        modified = sum(1 for line in lines[1:] if line and line[1] in "MD")
        untracked = sum(1 for line in lines[1:] if line and line.startswith("??"))

        result = f"""Git repository status:
Branch: {branch}
Staged files: {staged}
Modified files: {modified}
Untracked files: {untracked}

"""
        if len(lines) > 1:
            result += "Details:\n" + "\n".join(lines[1:])
        else:
            result += "Clean working tree"

        return result

    except Exception as e:
        return f"ERROR executing git status: {e!s}"


async def git_add(files: str | list[str], path: str | None = None) -> str:
    """
    Adds files to the git staging area.

    Args:
        files: File(s) to add (string or list of strings)
        path: Repository path (uses current directory if not specified)

    Returns:
        str: Operation result
    """
    work_dir = path or os.getcwd()

    if isinstance(files, str):
        files = [files]

    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "add",
            *files,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        return f"✓ Files added successfully: {', '.join(files)}"

    except Exception as e:
        return f"ERROR executing git add: {e!s}"


async def git_commit(message: str, path: str | None = None) -> str:
    """
    Creates a commit with staged changes.

    Args:
        message: Commit message
        path: Repository path (uses current directory if not specified)

    Returns:
        str: Commit result including hash
    """
    work_dir = path or os.getcwd()

    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "commit",
            "-m",
            message,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode("utf-8", errors="replace")
        return f"✓ Commit created successfully:\n{output}"

    except Exception as e:
        return f"ERROR executing git commit: {e!s}"


async def git_push(remote: str = "origin", branch: str | None = None, path: str | None = None) -> str:
    """
    Pushes commits to the remote repository.

    Args:
        remote: Remote name (default: origin)
        branch: Branch name (uses current if not specified)
        path: Repository path (uses current directory if not specified)

    Returns:
        str: Push result
    """
    work_dir = path or os.getcwd()

    try:
        command = ["git", "push", remote]
        if branch:
            command.append(branch)

        proc = await asyncio.create_subprocess_exec(
            *command, cwd=work_dir, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        # Git push writes information to stderr even when successful
        output = stderr.decode("utf-8", errors="replace") + stdout.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            return f"ERROR in git push:\n{output}"

        return f"✓ Push successful:\n{output}"

    except Exception as e:
        return f"ERROR executing git push: {e!s}"


async def git_pull(remote: str = "origin", branch: str | None = None, path: str | None = None) -> str:
    """
    Pulls changes from the remote repository.

    Args:
        remote: Remote name (default: origin)
        branch: Branch name (uses current if not specified)
        path: Repository path (uses current directory if not specified)

    Returns:
        str: Pull result
    """
    work_dir = path or os.getcwd()

    try:
        command = ["git", "pull", remote]
        if branch:
            command.append(branch)

        proc = await asyncio.create_subprocess_exec(
            *command, cwd=work_dir, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        output = stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            return f"ERROR in git pull:\n{output}"

        return f"✓ Pull successful:\n{output}"

    except Exception as e:
        return f"ERROR executing git pull: {e!s}"


async def git_log(limit: int = 10, path: str | None = None) -> str:
    """
    Shows the commit history.

    Args:
        limit: Maximum number of commits to show
        path: Repository path (uses current directory if not specified)

    Returns:
        str: List of recent commits
    """
    work_dir = path or os.getcwd()

    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "log",
            f"-{limit}",
            "--oneline",
            "--decorate",
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode("utf-8", errors="replace")
        return f"Last {limit} commits:\n{output}"

    except Exception as e:
        return f"ERROR executing git log: {e!s}"


async def git_branch(operation: str = "list", branch_name: str | None = None, path: str | None = None) -> str:
    """
    Manages git branches.

    Args:
        operation: Operation to perform ('list', 'create', 'delete', 'switch')
        branch_name: Branch name (required for create, delete, switch)
        path: Repository path (uses current directory if not specified)

    Returns:
        str: Operation result
    """
    work_dir = path or os.getcwd()

    try:
        if operation == "list":
            command = ["git", "branch", "-a"]
        elif operation == "create" and branch_name:
            command = ["git", "branch", branch_name]
        elif operation == "delete" and branch_name:
            command = ["git", "branch", "-d", branch_name]
        elif operation == "switch" and branch_name:
            command = ["git", "checkout", branch_name]
        else:
            return f"ERROR: Invalid operation '{operation}' or missing branch_name"

        proc = await asyncio.create_subprocess_exec(
            *command, cwd=work_dir, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode("utf-8", errors="replace")
        return output if output else f"✓ Operation '{operation}' completed"

    except Exception as e:
        return f"ERROR executing git branch: {e!s}"


async def git_diff(cached: bool = False, path: str | None = None) -> str:
    """
    Shows the differences in the repository.

    Args:
        cached: If True, shows diff of staged changes
        path: Repository path (uses current directory if not specified)

    Returns:
        str: Diff of changes
    """
    work_dir = path or os.getcwd()

    try:
        command = ["git", "diff"]
        if cached:
            command.append("--cached")

        proc = await asyncio.create_subprocess_exec(
            *command, cwd=work_dir, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode("utf-8", errors="replace")
        if not output:
            return "No changes to show"

        return f"Differences {'(staged)' if cached else '(working tree)'}:\n{output}"

    except Exception as e:
        return f"ERROR executing git diff: {e!s}"
