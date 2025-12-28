import os


async def delete_file(target_file: str, explanation: str = "") -> str:
    """
    Delete a file at the specified path.

    Parameters:
        target_file (str): The path to the file to be deleted
        explanation (str): Optional explanation for the deletion operation

    Returns:
        str: Success message if file deleted, error message if not found or failed
    """
    try:
        if os.path.exists(target_file):
            os.remove(target_file)
            return f"Successfully deleted file: {target_file}"
        else:
            return f"File not found: {target_file}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"
