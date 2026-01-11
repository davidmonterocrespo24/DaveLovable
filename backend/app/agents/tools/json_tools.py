"""
JSON File Tools - AutoGen Format
"""

import json
import logging
from typing import Any


async def read_json(filepath: str, encoding: str = "utf-8") -> dict[str, Any] | list[Any]:
    """
    Reads a JSON file and returns its contents.

    Args:
        filepath: Path to the JSON file
        encoding: File encoding (default: utf-8)

    Returns:
        Dict or List: Contents of the JSON file
    """
    try:
        with open(filepath, encoding=encoding) as f:
            data = json.load(f)
        return data
    except Exception as e:
        error_msg = f"Error reading JSON file {filepath}: {e!s}"
        logging.error(error_msg)
        return {"error": error_msg}


async def write_json(
    filepath: str,
    data: dict[str, Any] | list[Any],
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False,
) -> str:
    """
    Writes data to a JSON file.

    Args:
        filepath: Output file path
        data: Data to write (dict or list)
        encoding: File encoding (default: utf-8)
        indent: Spaces for indentation (default: 2)
        ensure_ascii: Escape non-ASCII characters (default: False)

    Returns:
        str: Success or error message
    """
    try:
        with open(filepath, "w", encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        return f"✓ JSON file saved successfully to {filepath}"
    except Exception as e:
        error_msg = f"Error writing JSON file {filepath}: {e!s}"
        logging.error(error_msg)
        return error_msg


async def merge_json_files(file1: str, file2: str, output_file: str, overwrite_duplicates: bool = True) -> str:
    """
    Merges two JSON files.

    Args:
        file1: First JSON file
        file2: Second JSON file
        output_file: Output file
        overwrite_duplicates: Overwrite duplicate keys with values from file2

    Returns:
        str: Success or error message
    """
    try:
        # Read both files
        data1 = await read_json(file1)
        data2 = await read_json(file2)

        if isinstance(data1, dict) and "error" in data1:
            return str(data1["error"])
        if isinstance(data2, dict) and "error" in data2:
            return str(data2["error"])

        # Merge
        result: dict[str, Any] | list[Any]
        if isinstance(data1, dict) and isinstance(data2, dict):
            if overwrite_duplicates:
                result = {**data1, **data2}
            else:
                result = data1.copy()
                for key, value in data2.items():
                    if key not in result:
                        result[key] = value
        elif isinstance(data1, list) and isinstance(data2, list):
            result = data1 + data2
        else:
            return f"ERROR: Cannot merge incompatible types: {type(data1).__name__} and {type(data2).__name__}"

        # Write result
        return await write_json(output_file, result)

    except Exception as e:
        error_msg = f"Error merging JSON files: {e!s}"
        logging.error(error_msg)
        return error_msg


async def validate_json(filepath: str) -> str:
    """
    Validates that a file has valid JSON format.

    Args:
        filepath: Path to the JSON file

    Returns:
        str: Message indicating whether it's valid or not
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            json.load(f)
        return f"✓ {filepath} is a valid JSON"
    except json.JSONDecodeError as e:
        return f"ERROR: Invalid JSON in {filepath}: {e!s}"
    except Exception as e:
        return f"ERROR: {e!s}"


async def format_json(filepath: str, indent: int = 2) -> str:
    """
    Formats a JSON file with consistent indentation.

    Args:
        filepath: Path to the JSON file
        indent: Spaces for indentation

    Returns:
        str: Success or error message
    """
    try:
        # Read file
        data = await read_json(filepath)
        if isinstance(data, dict) and "error" in data:
            return str(data["error"])

        # Rewrite with format
        return await write_json(filepath, data, indent=indent)

    except Exception as e:
        error_msg = f"Error formatting JSON: {e!s}"
        logging.error(error_msg)
        return error_msg


async def json_get_value(filepath: str, key_path: str) -> str:
    """
    Gets a value from a JSON file using a key path.

    Args:
        filepath: Path to the JSON file
        key_path: Dot-separated key path (e.g.: "user.name")

    Returns:
        str: Found value or error message
    """
    try:
        data = await read_json(filepath)
        if isinstance(data, dict) and "error" in data:
            return str(data["error"])

        # Navigate through keys
        keys = key_path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict):
                if key in current:
                    current = current[key]
                else:
                    return f"ERROR: Key '{key}' not found"
            elif isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index]
                except (ValueError, IndexError):
                    return f"ERROR: Index '{key}' invalid or out of range"
            else:
                return f"ERROR: Cannot navigate in type {type(current).__name__}"

        return f"Value at '{key_path}': {json.dumps(current, indent=2, ensure_ascii=False)}"

    except Exception as e:
        return f"ERROR: {e!s}"


async def json_set_value(filepath: str, key_path: str, value: str) -> str:
    """
    Sets a value in a JSON file using a key path.

    Args:
        filepath: Path to the JSON file
        key_path: Dot-separated key path (e.g.: "user.name")
        value: Value to set (as JSON string)

    Returns:
        str: Success or error message
    """
    try:
        data = await read_json(filepath)
        if isinstance(data, dict) and "error" in data:
            return str(data["error"])

        # Parse the value
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            # If not valid JSON, use as string
            parsed_value = value

        # Navigate and set value
        keys = key_path.split(".")
        current = data

        for key in keys[:-1]:
            if isinstance(current, dict):
                if key not in current:
                    current[key] = {}
                current = current[key]
            else:
                return f"ERROR: Cannot navigate in type {type(current).__name__}"

        # Set final value
        last_key = keys[-1]
        if isinstance(current, dict):
            current[last_key] = parsed_value
        else:
            return f"ERROR: Cannot set value in type {type(current).__name__}"

        # Save changes
        return await write_json(filepath, data)

    except Exception as e:
        return f"ERROR: {e!s}"


async def json_to_text(filepath: str, pretty: bool = True) -> str:
    """
    Converts a JSON file to readable text.

    Args:
        filepath: Path to the JSON file
        pretty: If True, formats with indentation

    Returns:
        str: JSON content as text
    """
    try:
        data = await read_json(filepath)
        if isinstance(data, dict) and "error" in data:
            return str(data["error"])

        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        return f"ERROR: {e!s}"
