from pathlib import Path

from app.agents.tools.common import HIDDEN_DIRS, get_workspace


async def list_dir(target_dir: str = ".") -> str:
    """Lists files in a directory"""
    try:
        workspace = get_workspace()
        target = workspace / target_dir if not Path(target_dir).is_absolute() else Path(target_dir)

        result = f"Directory listing for {target}:\n"
        for item in sorted(target.iterdir()):
            # Skip hidden system directories
            if item.is_dir() and item.name in HIDDEN_DIRS:
                continue

            if item.is_dir():
                result += f"  [DIR]  {item.name}/\n"
            else:
                result += f"  [FILE] {item.name} ({item.stat().st_size} bytes)\n"
        return result
    except Exception as e:
        return f"Error listing directory: {e!s}"
