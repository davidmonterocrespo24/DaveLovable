# Agent Tools Documentation

This document describes the tool system implemented for the AutoGen agents in the Lovable Dev Clone application.

## Overview

The agent system now includes a comprehensive set of tools that allow agents to interact with the project files, execute commands, and perform various operations autonomously.

## Architecture

### Components

1. **tools/** - Core tool implementations organized by category
   - **file_operations.py** - File read, write, edit, delete, and list operations
   - **search_operations.py** - Glob, grep, and fuzzy file search
   - **terminal_operations.py** - Terminal command execution
   - **json_operations.py** - JSON file read, write, and validation
   - **__init__.py** - Package exports for easy importing
   - Each module returns standardized dictionaries with `success`, `data`, and `error` fields

2. **function_registry.py** - AutoGen function wrappers
   - Wraps tools with proper type annotations for AutoGen
   - Provides the `FUNCTION_MAP` that agents can call

3. **prompts.py** - Agent system prompts
   - Contains `AGENT_SYSTEM_PROMPT` with complete tool definitions
   - Includes usage guidelines and best practices

4. **orchestrator.py** - Agent initialization
   - Registers functions with the UserProxy agent
   - Makes tools available to all agents

## Available Tools

### File Operations

#### `read_file`
Read file contents with support for line ranges.
```python
read_file(
    target_file="path/to/file.py",
    should_read_entire_file=True,
    start_line_one_indexed=1,
    end_line_one_indexed_inclusive=None
)
```

#### `write_file`
Create or overwrite a file with content.
```python
write_file(
    target_file="path/to/file.py",
    file_content="def hello():\n    print('Hello')"
)
```

#### `edit_file`
Surgical edit of specific text blocks in files.
```python
edit_file(
    target_file="path/to/file.py",
    old_string="old code block",
    new_string="new code block",
    instructions="Fix bug in calculation"
)
```

#### `delete_file`
Delete a file from the filesystem.
```python
delete_file(target_file="path/to/file.py")
```

#### `list_dir`
List contents of a directory.
```python
list_dir(relative_workspace_path="src/components")
```

### Search Operations

#### `glob_search`
Search files by glob patterns.
```python
glob_search(
    pattern="**/*.ts",
    dir_path="src",
    case_sensitive=False
)
```

#### `grep_search`
Search for text/regex patterns within files.
```python
grep_search(
    query="function.*Component",
    include_pattern="*.tsx",
    case_sensitive=False
)
```

#### `file_search`
Fuzzy search for files by name.
```python
file_search(query="component")
```

### Data Operations

#### `read_json`
Read and parse JSON files.
```python
read_json(filepath="package.json", encoding="utf-8")
```

#### `write_json`
Write data to JSON files with formatting.
```python
write_json(
    filepath="config.json",
    data={"key": "value"},
    indent=2
)
```

### Terminal Operations

#### `run_terminal_cmd`
Execute terminal commands (requires user approval by default).
```python
run_terminal_cmd(
    command="npm install",
    is_background=False,
    require_user_approval=True
)
```

## How It Works

### 1. Agent Prompts
The `AGENT_SYSTEM_PROMPT` in `prompts.py` includes:
- Complete tool schemas in `<functions>` tags
- Usage guidelines in `<tool_calling>` section
- Best practices in `<making_code_changes>` section

### 2. Function Registration
During initialization in `orchestrator.py`:
```python
function_map = get_function_map()
self.user_proxy = UserProxyAgent(
    name="UserProxy",
    function_map=function_map,
)
self.coding_agent.register_function(function_map=function_map)
```

### 3. Tool Execution
When an agent wants to use a tool:
1. Agent generates a function call in its response
2. AutoGen's UserProxy agent executes the function
3. Function returns a result dictionary
4. Agent receives the result and continues

### 4. Response Format
All tools return standardized responses:
```python
{
    "success": True,
    "data": {...},  # Tool-specific data
    # OR
    "error": "Error message"
}
```

## Usage Examples

### Example 1: Agent Reads and Edits a File
```
User: "Fix the bug in the calculate function"

Agent: I'll read the file to see the current implementation.
[Calls: read_file(target_file="utils.py")]

[Receives content with bug]

Agent: I found the bug. I'll fix it now.
[Calls: edit_file(
    target_file="utils.py",
    old_string="result = a + b * c",
    new_string="result = (a + b) * c",
    instructions="Fix operator precedence"
)]

Agent: Fixed the bug by adding parentheses for correct order of operations.
```

### Example 2: Agent Searches and Creates Files
```
User: "Create a new React component"

Agent: Let me check the existing component structure.
[Calls: glob_search(pattern="src/components/**/*.tsx")]

[Receives list of component files]

Agent: I'll create the new component following the existing pattern.
[Calls: write_file(
    target_file="src/components/NewComponent.tsx",
    file_content="import React from 'react';\n\nexport const NewComponent = () => {...}"
)]

Agent: Component created successfully!
```

## Best Practices

### For Tool Implementers
1. **Return Standardized Responses**: Always include `success` field
2. **Handle Errors Gracefully**: Catch exceptions and return error messages
3. **Validate Inputs**: Check file paths and parameters before operations
4. **Provide Context**: Include useful metadata in responses

### For Agent Prompts
1. **Read Before Edit**: Always read files before making changes
2. **Use Surgical Edits**: Edit only what needs to change
3. **Provide Explanations**: Include instructions parameter for edits
4. **Verify Results**: Check tool responses for success

## Security Considerations

1. **User Approval Required**: Terminal commands require approval by default
2. **Path Validation**: Tools should validate file paths to prevent directory traversal
3. **Safe Defaults**: Operations default to safe mode
4. **Error Handling**: Tools fail gracefully without exposing system details

## Future Enhancements

Potential additions to the tool system:
- Git operations (commit, push, pull, branch)
- CSV file operations
- Wikipedia and web search tools
- Python code analysis tools
- More advanced file operations (move, copy, rename)

## Troubleshooting

### Tools Not Working
1. Check that `function_registry.py` is properly imported in `orchestrator.py`
2. Verify that the agent's LLM config includes the correct API key
3. Ensure AutoGen version supports function calling (pyautogen >= 0.2.0)

### Function Call Errors
1. Check that function signatures match the definitions in prompts.py
2. Verify parameter types match the annotations
3. Review agent logs for detailed error messages

## File Structure

```
backend/app/agents/
├── tools/
│   ├── __init__.py               # Package exports
│   ├── file_operations.py        # File CRUD operations
│   ├── search_operations.py      # Search tools (glob, grep, file_search)
│   ├── terminal_operations.py    # Terminal command execution
│   └── json_operations.py        # JSON read/write/validate
├── function_registry.py          # AutoGen function wrappers
├── prompts.py                    # Agent system prompts with tool schemas
├── config.py                     # Agent configuration
└── orchestrator.py               # Agent initialization and orchestration
```

## References

- AutoGen Documentation: https://microsoft.github.io/autogen/
- Tool Definitions: `backend/app/agents/prompts.py`
- Tool Implementations: `backend/app/agents/tools/`
- Function Registry: `backend/app/agents/function_registry.py`
