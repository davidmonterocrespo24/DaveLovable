import os

from app.agents.tools.common import EXCLUDED_DIRS


async def file_search(query: str, explanation: str = "") -> str:
    """
    Fast file search based on fuzzy matching against file path.

    Parameters:
        query (str): Search term to match against file paths
        explanation (str): Optional explanation for the search operation

    Returns:
        str: List of matching file paths (up to 10 results) or error message if search failed
    """
    try:
        matches = []

        for root, dirs, files in os.walk("."):
            # Filter out ignored directories IN-PLACE to prevent os.walk from descending into them
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                file_path = os.path.join(root, file)
                if query.lower() in file_path.lower():
                    matches.append(file_path)
                    if len(matches) >= 10:  # Cap at 10 results
                        break
            if len(matches) >= 10:
                break

        return f"File search results for '{query}':\n" + "\n".join(matches)
    except Exception as e:
        return f"Error in file search: {e!s}"
