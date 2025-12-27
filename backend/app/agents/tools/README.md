# Agent Tools

This directory contains all the tools that AutoGen agents can use to perform operations on the project.

## Structure

Each file contains related tools for specific operations:

### file_operations.py
File system operations for reading, writing, editing, and managing files.

**Tools:**
- `read_file()` - Read file contents with line range support
- `write_file()` - Create or overwrite files
- `edit_file()` - Surgically edit specific text blocks
- `delete_file()` - Delete files
- `list_dir()` - List directory contents

### search_operations.py
Search tools for finding files and content.

**Tools:**
- `glob_search()` - Search files by glob patterns (e.g., `**/*.py`)
- `grep_search()` - Search for text/regex patterns within files
- `file_search()` - Fuzzy search for files by name

### terminal_operations.py
Terminal command execution tools.

**Tools:**
- `run_terminal_cmd()` - Execute terminal commands (requires user approval)

### json_operations.py
JSON file manipulation tools.

**Tools:**
- `read_json()` - Read and parse JSON files
- `write_json()` - Write data to JSON files with formatting
- `validate_json()` - Validate JSON file syntax

## Usage

All tools follow a consistent pattern:

1. **Import**: Tools are exported via `__init__.py`
   ```python
   from app.agents.tools import read_file, write_file
   ```

2. **Call**: Each tool returns a standardized response
   ```python
   result = read_file(target_file="example.py")
   if result["success"]:
       content = result["content"]
   else:
       error = result["error"]
   ```

3. **Response Format**: All tools return dictionaries with:
   ```python
   {
       "success": bool,          # True if operation succeeded
       "data": {...},            # Tool-specific data (if success)
       "error": str,             # Error message (if failure)
       # ... additional tool-specific fields
   }
   ```

## Adding New Tools

To add a new tool:

1. **Choose the right file** or create a new category file
2. **Implement the tool function** with proper error handling
3. **Return standardized response** with `success`, `data`, and `error`
4. **Export in `__init__.py`** to make it available
5. **Register in `function_registry.py`** with type annotations
6. **Update `prompts.py`** with the tool schema in `<functions>` section

## Best Practices

### For Tool Implementers
- Always return `{"success": bool, ...}` structure
- Handle all exceptions gracefully
- Provide descriptive error messages
- Include useful metadata in responses
- Validate inputs before operations
- Use `os.path` or `pathlib` for cross-platform paths

### For Security
- Validate all file paths to prevent directory traversal
- Default to safe operations (require approval for dangerous commands)
- Don't expose system details in error messages
- Use timeouts for subprocess operations
- Sanitize user inputs

## Examples

### File Operations
```python
# Read a file
result = read_file(target_file="src/app.py", should_read_entire_file=True)

# Write a new file
result = write_file(
    target_file="src/new_module.py",
    file_content="def hello():\n    print('Hello')"
)

# Edit existing file
result = edit_file(
    target_file="src/app.py",
    old_string="def old_function():",
    new_string="def new_function():",
    instructions="Rename function for clarity"
)
```

### Search Operations
```python
# Find all Python files
result = glob_search(pattern="**/*.py")

# Search for text in files
result = grep_search(
    query="import.*React",
    include_pattern="*.tsx"
)

# Find files by name
result = file_search(query="component")
```

### JSON Operations
```python
# Read JSON config
result = read_json(filepath="package.json")

# Write JSON data
result = write_json(
    filepath="config.json",
    data={"setting": "value"},
    indent=2
)
```

## Testing

Each tool should be tested for:
- ✅ Success cases with valid inputs
- ✅ Error handling for invalid inputs
- ✅ Edge cases (empty files, missing directories, etc.)
- ✅ Cross-platform compatibility (Windows/Linux/Mac)
- ✅ Security considerations (path traversal, command injection)

## Troubleshooting

### Common Issues

**Import errors**: Make sure `__init__.py` exports the tool
**Type errors**: Check that function signatures match `function_registry.py`
**Permission errors**: Verify file/directory permissions
**Path errors**: Use absolute paths or verify working directory

## Related Files

- `../function_registry.py` - AutoGen function wrappers with type annotations
- `../prompts.py` - Tool schemas for agent prompts
- `../orchestrator.py` - Tool registration with agents
- `../../AGENT_TOOLS.md` - Complete documentation
