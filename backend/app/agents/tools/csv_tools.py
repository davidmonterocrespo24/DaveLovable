"""
CSV File Tools - AutoGen Format
"""

import logging
from importlib import util


def _check_pandas():
    """Checks if pandas is installed"""
    if util.find_spec("pandas") is None:
        raise ImportError("pandas package not available. Install with: pip install pandas")
    import pandas as pd

    return pd


async def read_csv(filepath: str, delimiter: str = ",", encoding: str = "utf-8", max_rows: int = None) -> str:
    """
    Reads a CSV file and returns its contents.

    Args:
        filepath: Path to the CSV file
        delimiter: Column delimiter (default: ',')
        encoding: File encoding (default: utf-8)
        max_rows: Maximum number of rows to read (None = all)

    Returns:
        str: CSV contents in readable format
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding, nrows=max_rows)

        output = f"CSV: {filepath}\n"
        output += f"Rows: {len(df)}, Columns: {len(df.columns)}\n\n"
        output += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        output += "First rows:\n"
        output += df.head(10).to_string()

        if len(df) > 10:
            output += f"\n\n... (showing 10 of {len(df)} rows)"

        return output

    except Exception as e:
        error_msg = f"Error reading CSV {filepath}: {e!s}"
        logging.error(error_msg)
        return error_msg


async def write_csv(filepath: str, data: str, delimiter: str = ",", mode: str = "w", encoding: str = "utf-8") -> str:
    """
    Writes data to a CSV file.

    Args:
        filepath: Output file path
        data: Data in CSV format (string with delimiters)
        delimiter: Column delimiter (default: ',')
        mode: Write mode ('w' = overwrite, 'a' = append)
        encoding: File encoding (default: utf-8)

    Returns:
        str: Success or error message
    """
    try:
        # Write string directly as CSV
        with open(filepath, mode, encoding=encoding, newline="") as f:
            f.write(data)
            if not data.endswith("\n"):
                f.write("\n")

        return f"✓ Data written to {filepath}"

    except Exception as e:
        error_msg = f"Error writing CSV {filepath}: {e!s}"
        logging.error(error_msg)
        return error_msg


async def csv_info(filepath: str, delimiter: str = ",", encoding: str = "utf-8") -> str:
    """
    Gets statistical information about a CSV file.

    Args:
        filepath: Path to the CSV file
        delimiter: Column delimiter
        encoding: File encoding

    Returns:
        str: Statistical information about the CSV
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)

        output = f"=== Information for {filepath} ===\n\n"
        output += f"Dimensions: {len(df)} rows x {len(df.columns)} columns\n\n"

        output += "Columns and types:\n"
        for col in df.columns:
            output += f"  - {col}: {df[col].dtype}\n"

        output += "\nNull values:\n"
        nulls = df.isnull().sum()
        if nulls.sum() == 0:
            output += "  No null values\n"
        else:
            for col in nulls[nulls > 0].index:
                output += f"  - {col}: {nulls[col]} nulls\n"

        output += "\nNumeric statistics:\n"
        numeric_df = df.select_dtypes(include=["number"])
        if not numeric_df.empty:
            output += numeric_df.describe().to_string()
        else:
            output += "  No numeric columns\n"

        return output

    except Exception as e:
        error_msg = f"Error getting CSV info {filepath}: {e!s}"
        logging.error(error_msg)
        return error_msg


async def filter_csv(filepath: str, column: str, value: str, output_file: str = None, delimiter: str = ",") -> str:
    """
    Filters a CSV by a column value.

    Args:
        filepath: Path to the CSV file
        column: Name of the column to filter
        value: Value to search for
        output_file: Output file (None = return as text)
        delimiter: Column delimiter

    Returns:
        str: Filtered result or success message
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(filepath, delimiter=delimiter)

        if column not in df.columns:
            return f"ERROR: Column '{column}' does not exist. Available columns: {', '.join(df.columns)}"

        # Filter
        filtered_df = df[df[column].astype(str).str.contains(value, case=False, na=False)]

        if len(filtered_df) == 0:
            return f"No rows found with '{value}' in column '{column}'"

        if output_file:
            filtered_df.to_csv(output_file, index=False, sep=delimiter)
            return f"✓ {len(filtered_df)} filtered rows saved to {output_file}"
        else:
            output = f"Filtered: {len(filtered_df)} rows with '{value}' in '{column}':\n\n"
            output += filtered_df.to_string()
            return output

    except Exception as e:
        error_msg = f"Error filtering CSV: {e!s}"
        logging.error(error_msg)
        return error_msg


async def merge_csv_files(file1: str, file2: str, output_file: str, on_column: str = None, how: str = "inner") -> str:
    """
    Merges two CSV files.

    Args:
        file1: First CSV file
        file2: Second CSV file
        output_file: Output file
        on_column: Column to merge on (None = concatenate)
        how: Type of merge ('inner', 'outer', 'left', 'right')

    Returns:
        str: Success or error message
    """
    try:
        pd = _check_pandas()

        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        if on_column:
            # Merge by column
            if on_column not in df1.columns:
                return f"ERROR: Column '{on_column}' does not exist in {file1}"
            if on_column not in df2.columns:
                return f"ERROR: Column '{on_column}' does not exist in {file2}"

            result = pd.merge(df1, df2, on=on_column, how=how)
            operation = f"merge on '{on_column}' (type: {how})"
        else:
            # Concatenate vertically
            result = pd.concat([df1, df2], ignore_index=True)
            operation = "concatenation"

        result.to_csv(output_file, index=False)

        return f"✓ Files merged ({operation})\n  Result: {len(result)} rows x {len(result.columns)} columns\n  Saved to: {output_file}"

    except Exception as e:
        error_msg = f"Error merging CSVs: {e!s}"
        logging.error(error_msg)
        return error_msg


async def csv_to_json(csv_file: str, json_file: str, orient: str = "records") -> str:
    """
    Converts a CSV file to JSON.

    Args:
        csv_file: Input CSV file
        json_file: Output JSON file
        orient: JSON orientation ('records', 'index', 'columns', 'values')

    Returns:
        str: Success or error message
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(csv_file)
        df.to_json(json_file, orient=orient, indent=2)

        return f"✓ CSV converted to JSON\n  {len(df)} rows exported to {json_file}"

    except Exception as e:
        error_msg = f"Error converting CSV to JSON: {e!s}"
        logging.error(error_msg)
        return error_msg


async def sort_csv(filepath: str, column: str, output_file: str = None, ascending: bool = True) -> str:
    """
    Sorts a CSV file by a column.

    Args:
        filepath: CSV file
        column: Column to sort by
        output_file: Output file (None = overwrite original)
        ascending: True for ascending, False for descending

    Returns:
        str: Success or error message
    """
    try:
        pd = _check_pandas()

        df = pd.read_csv(filepath)

        if column not in df.columns:
            return f"ERROR: Column '{column}' does not exist. Columns: {', '.join(df.columns)}"

        df_sorted = df.sort_values(by=column, ascending=ascending)

        output = output_file or filepath
        df_sorted.to_csv(output, index=False)

        direction = "ascendente" if ascending else "descendente"
        return f"✓ CSV ordenado por '{column}' ({direction})\n  Guardado en: {output}"

    except Exception as e:
        error_msg = f"Error ordenando CSV: {e!s}"
        logging.error(error_msg)
        return error_msg
