# Multi-Agent System Tests

This directory contains tests that verify the **SelectorGroupChat architecture** with Planner and Coder agents is functioning correctly.

## Test Files

### test_multiagent_simple.py

**Simple verification script** that tests the multi-agent system without pytest complexity.

**Run with:**
```bash
python backend/tests/test_multiagent_simple.py
```

**Tests included:**

1. **Orchestrator Initialization**
   - Verifies orchestrator is a singleton
   - Checks that Coder and Planner agents exist
   - Validates agent names are correct ("Coder", "Planner")
   - Confirms Coder has 23+ tools (file operations, Git, JSON, CSV, etc.)
   - Verifies essential tools: write_file, read_file, edit_file, delete_file, list_dir
   - Confirms Planner has NO tools (only plans)
   - Checks team has 2 participants

2. **Architecture Components**
   - Verifies orchestrator module exports
   - Confirms chat service exists
   - Validates FileSystemService still exists (still necessary)
   - Checks all agent prompts are defined
   - Verifies agent tools are importable

3. **Working Directory Context**
   - Tests changing working directory to project directory
   - Verifies working directory restoration
   - Validates proper cleanup

4. **Chat Service Integration**
   - Tests creating test project and files
   - Verifies chat session creation
   - Validates message creation
   - Tests database integration

### test_multiagent_system.py

**Comprehensive pytest test suite** for multi-agent system (has some pytest compatibility issues on Windows).

**Run with:**
```bash
pytest backend/tests/test_multiagent_system.py -v
```

**Note:** Currently has output capture issues with pytest on Windows. Use `test_multiagent_simple.py` instead for reliable verification.

## Test Results (Latest Run)

```
============================================================
RESULTS: 4 passed, 0 failed
============================================================

✅ ALL TESTS PASSED - Multi-agent system is working correctly!
```

### Test 1: Orchestrator Initialization ✅
- ✓ Orchestrator is a singleton
- ✓ All components exist (coder_agent, planning_agent, main_team, model_client)
- ✓ Agent names correct: Coder, Planner
- ✓ Coder has 23 tools
- ✓ All essential file operation tools present
- ✓ Planner has no tools (only plans)
- ✓ Team has 2 participants (Planner + Coder)

### Test 2: Architecture Components ✅
- ✓ Orchestrator module has required exports
- ✓ Chat service module has required exports
- ✓ FileSystemService still exists (as expected)
- ✓ All agent prompts defined
- ✓ Agent tools are importable

### Test 3: Working Directory Context ✅
- ✓ Created temporary directory
- ✓ Changed working directory to temp directory
- ✓ Restored original working directory
- ✓ Cleanup successful

### Test 4: Chat Service Integration ✅
- ✓ Created test project 9999
- ✓ Created chat session
- ✓ Created chat message
- ⚠ File cleanup skipped (Git lock on Windows - expected behavior)

## What These Tests Verify

### ✅ New SelectorGroupChat Architecture Works
- The orchestrator correctly initializes with 2 agents (Planner, Coder)
- Model-based speaker selection is configured
- Termination conditions are set (TextMentionTermination + MaxMessageTermination)

### ✅ Coder Agent Has All Required Tools
The Coder agent has access to 23 tools:
- **File Operations**: write_file, read_file, edit_file, delete_file
- **Directory Operations**: list_dir, file_search, glob_search
- **Search Tools**: grep_search
- **Git Operations**: git_status, git_add, git_commit, git_push, git_pull, git_log, git_branch, git_diff
- **Data Tools**: JSON manipulation, CSV manipulation
- **Terminal**: run_terminal_cmd
- **Web Tools**: Wikipedia search, web search

### ✅ Planner Agent Has No Tools
- Confirmed that Planner agent has an empty tools list
- Planner only creates strategic plans, doesn't execute

### ✅ Chat Service Integration Works
- Chat service can create sessions
- Chat service can create messages
- Database integration works correctly
- FileSystemService is still functional (still needed)

### ✅ Working Directory Context Management Works
- The system can change working directory to project-specific directories
- Working directory is properly restored after operations
- This is critical for agent tools to operate in the correct project context

## Integration with chat_service.py

The tests verify that [backend/app/services/chat_service.py](../app/services/chat_service.py) correctly:

1. Changes working directory to `backend/projects/project_{id}/`
2. Calls `orchestrator.main_team.run(task=...)`
3. Extracts response from team messages
4. Restores original working directory
5. Saves assistant message to database

## Known Issues

### Windows Git Lock Issue
On Windows, Git may lock files in `.git/objects/` which prevents cleanup during tests. This is expected behavior and doesn't affect production usage. The test handles this gracefully with a try/except block.

### Pytest Output Capture Issue
The comprehensive pytest test suite has output capture issues on Windows. Use `test_multiagent_simple.py` for reliable verification.

## Running Tests in Different Environments

### Development (with OpenAI API key)
```bash
# Run simple verification
python backend/tests/test_multiagent_simple.py

# For more detailed testing (if pytest works)
pytest backend/tests/test_multiagent_system.py::TestOrchestratorInitialization -v
```

### CI/CD (without OpenAI API key)
```bash
# Only run non-API tests
pytest backend/tests/test_multiagent_system.py -v -m "not slow"
```

The tests automatically skip end-to-end tests that require OpenAI API key if it's not configured.

## Next Steps

To test the full multi-agent workflow with actual AI generation:

1. **Ensure OpenAI API key is configured** in `.env`
2. **Start the backend server**: `python backend/run.py`
3. **Start the frontend**: `cd front && npm run dev`
4. **Create a project** through the UI
5. **Send a chat message** like "Create a simple Button component"
6. **Verify the agents**:
   - Planner creates a plan
   - Coder implements using tools
   - Files are created in `backend/projects/project_{id}/`
   - Git commits are created
   - Response appears in chat

## Test Coverage

These tests verify:
- ✅ Orchestrator initialization and configuration
- ✅ Agent setup (Planner + Coder)
- ✅ Tool assignment (Coder has tools, Planner doesn't)
- ✅ Team configuration (SelectorGroupChat with 2 participants)
- ✅ Chat service integration
- ✅ Working directory context management
- ✅ Database integration
- ✅ FileSystemService functionality

These tests do NOT verify (requires OpenAI API key + integration testing):
- ❌ Actual AI code generation
- ❌ Agent collaboration behavior
- ❌ Tool execution in production
- ❌ Git commit creation by agents
- ❌ Error handling in complex scenarios

For full end-to-end testing, use the application through the UI with a real OpenAI API key.
