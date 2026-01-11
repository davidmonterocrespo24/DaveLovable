"""
Code Analysis Tools - AutoGen Format
Analyzes Python file structure to extract functions, classes, and imports
"""

import ast
from pathlib import Path
from typing import Any


async def analyze_python_file(filepath: str) -> str:
    """
    Analyzes a Python file and extracts its structure (functions, classes, imports).

    Args:
        filepath: Path to the Python file

    Returns:
        str: Detailed file analysis
    """
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return f"ERROR: File not found: {filepath}"

        if not filepath.endswith(".py"):
            return f"ERROR: {filepath} is not a Python file (.py)"

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=filepath)

        # Extract information
        imports = _extract_imports(tree)
        classes = _extract_classes(tree, content)
        functions = _extract_functions(tree, content)

        # Format output
        output = f"=== Analysis of {file_path.name} ===\n\n"
        output += f"Lines of code: {len(content.splitlines())}\n\n"

        if imports:
            output += f"IMPORTS ({len(imports)}):\n"
            for imp in imports:
                if imp["type"] == "import":
                    output += f"  import {imp['module']}\n"
                else:
                    output += f"  from {imp['module']} import {imp['name']}\n"
            output += "\n"

        if classes:
            output += f"CLASSES ({len(classes)}):\n"
            for cls in classes:
                output += f"  class {cls['name']}:\n"
                output += f"    Lines: {cls['line_start']}-{cls['line_end']}\n"
                if cls["bases"]:
                    output += f"    Inherits from: {', '.join(cls['bases'])}\n"
                output += f"    Methods: {len(cls['methods'])}\n"
                for method in cls["methods"]:
                    output += f"      - {method['name']}()\n"
                output += "\n"

        if functions:
            output += f"FUNCTIONS ({len(functions)}):\n"
            for func in functions:
                if not func["is_method"]:  # Only top-level functions
                    output += f"  {func['signature']}\n"
                    output += f"    Lines: {func['line_start']}-{func['line_end']}\n"
                    if func.get("docstring"):
                        doc = func["docstring"].split("\n")[0][:60]
                        output += f"    Doc: {doc}...\n"
                    output += "\n"

        return output

    except SyntaxError as e:
        return f"ERROR: Invalid syntax in {filepath}:\n  Line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"ERROR analyzing {filepath}: {e!s}"


async def find_function_definition(filepath: str, function_name: str) -> str:
    """
    Finds the definition of a function in a Python file.

    Args:
        filepath: Path to the Python file
        function_name: Name of the function to search for

    Returns:
        str: Function code or error message
    """
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return f"ERROR: File not found: {filepath}"

        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()

        tree = ast.parse(content, filename=filepath)
        functions = _extract_functions(tree, content)

        # Search for function
        for func in functions:
            if func["name"] == function_name:
                start = func["line_start"] - 1
                end = func["line_end"]

                func_code = "\n".join(lines[start:end])

                output = f"Function '{function_name}' in {file_path.name}:\n"
                output += f"Lines: {func['line_start']}-{func['line_end']}\n"
                output += f"Signature: {func['signature']}\n\n"
                output += "Code:\n"
                output += func_code

                return output

        return f"ERROR: Function '{function_name}' not found in {filepath}"

    except Exception as e:
        return f"ERROR: {e!s}"


async def list_all_functions(filepath: str) -> str:
    """
    Lists all functions in a Python file.

    Args:
        filepath: Path to the Python file

    Returns:
        str: List of functions with their signatures
    """
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return f"ERROR: File not found: {filepath}"

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=filepath)
        functions = _extract_functions(tree, content)

        if not functions:
            return f"No functions found in {filepath}"

        output = f"=== Functions in {file_path.name} ===\n\n"
        for func in functions:
            prefix = "  Method" if func["is_method"] else "Function"
            output += f"{prefix}: {func['signature']}\n"
            output += f"  Lines: {func['line_start']}-{func['line_end']}\n"
            if func.get("docstring"):
                doc = func["docstring"].split("\n")[0][:70]
                output += f"  {doc}\n"
            output += "\n"

        return output

    except Exception as e:
        return f"ERROR: {e!s}"


def _extract_imports(tree: ast.AST) -> list[dict[str, Any]]:
    """Extracts imports from AST"""
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    {
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(
                    {
                        "type": "from",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                    }
                )

    return imports


def _extract_classes(tree: ast.AST, content: str) -> list[dict[str, Any]]:
    """Extracts classes from AST"""
    classes = []

    class ClassVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            class_info = {
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "docstring": ast.get_docstring(node),
                "bases": [ast.unparse(base) for base in node.bases],
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "methods": [],
            }

            # Get methods
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    class_info["methods"].append(
                        {
                            "name": item.name,
                            "line": item.lineno,
                            "is_async": isinstance(item, ast.AsyncFunctionDef),
                        }
                    )

            classes.append(class_info)
            self.generic_visit(node)

    visitor = ClassVisitor()
    visitor.visit(tree)
    return classes


def _extract_functions(tree: ast.AST, content: str) -> list[dict[str, Any]]:
    """Extracts functions from AST"""
    functions = []
    lines = content.splitlines()

    class FunctionVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_class = None

        def visit_ClassDef(self, node):
            old_class = self.current_class
            self.current_class = node.name
            self.generic_visit(node)
            self.current_class = old_class

        def visit_FunctionDef(self, node):
            func_info = {
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "signature": _get_function_signature(node),
                "docstring": ast.get_docstring(node),
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "is_method": self.current_class is not None,
                "class_name": self.current_class,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            }

            # Return type si existe
            if node.returns:
                func_info["return_type"] = ast.unparse(node.returns)

            functions.append(func_info)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

    visitor = FunctionVisitor()
    visitor.visit(tree)
    return functions


def _get_function_signature(node: ast.FunctionDef) -> str:
    """Gets the function signature"""
    args = []

    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args.append(arg_str)

    # Defaults
    defaults_start = len(args) - len(node.args.defaults)
    for i, default in enumerate(node.args.defaults):
        args[defaults_start + i] += f"={ast.unparse(default)}"

    # *args y **kwargs
    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")

    signature = f"{node.name}({', '.join(args)})"

    # Return type
    if node.returns:
        signature += f" -> {ast.unparse(node.returns)}"

    return signature
