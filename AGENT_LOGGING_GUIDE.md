# Agent Logging Guide - Multi-Agent System

## Overview

The multi-agent system now includes **detailed logging** that shows all agent interactions, tool calls, and conversations in real-time in the backend console.

## What's Logged

### 1. Execution Start
```
================================================================================
🤖 STARTING MULTI-AGENT TEAM EXECUTION
================================================================================
📝 User Request: Create a simple Button component
📁 Project Files: 8
================================================================================
```

### 2. Working Directory Context
```
📂 Changed working directory to: E:\AI\DaveLovable\DaveLovable\backend\projects\project_1
```

### 3. Agent Messages
For each message in the conversation:
```
────────────────────────────────────────────────────────────────────────────────
💬 Message 1/5 - From: Planner
────────────────────────────────────────────────────────────────────────────────
   Let me create a plan for implementing the Button component:

   1. Create the Button component file (src/components/Button.tsx)
   2. Implement TypeScript interface for props
   3. Add Tailwind CSS styling
   4. Export the component
```

### 4. Tool Calls
When the Coder agent uses tools:
```
────────────────────────────────────────────────────────────────────────────────
💬 Message 2/5 - From: Coder
────────────────────────────────────────────────────────────────────────────────
🔧 TOOL CALL: write_file
   Arguments: {"target_file": "src/components/Button.tsx", "file_content": "..."}
```

### 5. Tool Responses
```
────────────────────────────────────────────────────────────────────────────────
💬 Message 3/5 - From: Tool
────────────────────────────────────────────────────────────────────────────────
   Successfully wrote 532 characters to src/components/Button.tsx
```

### 6. Final Response
```
================================================================================
📤 FINAL RESPONSE (from Coder):
================================================================================
I have successfully created the Button component. The component includes:
- TypeScript interface for props
- Multiple size and variant options
- Full Tailwind CSS styling
- Accessibility features
TASK_COMPLETED
================================================================================
```

### 7. Execution Complete
```
================================================================================
✅ MULTI-AGENT TEAM EXECUTION COMPLETED
================================================================================
📂 Restored working directory to: E:\AI\DaveLovable\DaveLovable\backend
```

## Error Logging

When errors occur:
```
================================================================================
❌ ERROR DURING AGENT EXECUTION
================================================================================
Error type: ValueError
Error message: API key not configured
================================================================================
Full traceback:
  File "app/services/chat_service.py", line 183, in process_chat_message
    result = await orchestrator.main_team.run(...)
  ...
```

## How to View Logs

### Development Mode

1. **Start the backend server:**
   ```bash
   cd backend
   python run.py
   ```

2. **Watch the console output** - all agent interactions will be logged in real-time

3. **Send a chat message** from the frontend, and you'll see:
   - When the agents start working
   - What the Planner says
   - What tools the Coder calls
   - What the tool responses are
   - The final response

### Example Output

```bash
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

# User sends message...

2025-01-15 10:30:45 - app.services.chat_service - INFO - ================================================================================
2025-01-15 10:30:45 - app.services.chat_service - INFO - 🤖 STARTING MULTI-AGENT TEAM EXECUTION
2025-01-15 10:30:45 - app.services.chat_service - INFO - ================================================================================
2025-01-15 10:30:45 - app.services.chat_service - INFO - 📝 User Request: Create a Button component
2025-01-15 10:30:45 - app.services.chat_service - INFO - 📁 Project Files: 8
2025-01-15 10:30:45 - app.services.chat_service - INFO - ================================================================================

# Agent conversation starts...

2025-01-15 10:30:50 - app.services.chat_service - INFO -
📨 Processing 5 messages from agents...

2025-01-15 10:30:50 - app.services.chat_service - INFO - ────────────────────────────────────────────────────────────────────────────────
2025-01-15 10:30:50 - app.services.chat_service - INFO - 💬 Message 1/5 - From: Planner
2025-01-15 10:30:50 - app.services.chat_service - INFO - ────────────────────────────────────────────────────────────────────────────────
2025-01-15 10:30:50 - app.services.chat_service - INFO -    I'll create a plan for the Button component...

... more messages ...

2025-01-15 10:30:55 - app.services.chat_service - INFO - ================================================================================
2025-01-15 10:30:55 - app.services.chat_service - INFO - ✅ MULTI-AGENT TEAM EXECUTION COMPLETED
2025-01-15 10:30:55 - app.services.chat_service - INFO - ================================================================================
```

## Logging Configuration

### Files Modified

1. **[backend/app/main.py](backend/app/main.py)** - Logging configuration
   - Configures root logger to INFO level
   - Sets chat_service logger to DEBUG for detailed output
   - Outputs to stdout (console)

2. **[backend/app/services/chat_service.py](backend/app/services/chat_service.py)** - Logging implementation
   - Logs execution start/end
   - Logs all agent messages
   - Logs tool calls and responses
   - Logs errors with full tracebacks

### Log Levels

```python
# Root logger
logging.basicConfig(level=logging.INFO)

# Chat service (detailed agent output)
logging.getLogger("app.services.chat_service").setLevel(logging.DEBUG)

# Agents module
logging.getLogger("app.agents").setLevel(logging.DEBUG)

# AutoGen library
logging.getLogger("autogen").setLevel(logging.INFO)
```

## What You'll See

### During Agent Execution

1. **Start marker** - When agents begin working
2. **User request** - What the user asked for
3. **Project context** - Files and working directory
4. **Planner messages** - Strategic plan from Planner agent
5. **Coder messages** - Implementation from Coder agent
6. **Tool calls** - Every file operation, Git command, etc.
7. **Tool responses** - Results from each tool
8. **Final response** - Summary from the agent
9. **Completion marker** - When execution finishes

### For Each Tool Call

```
🔧 TOOL CALL: write_file
   Arguments: {"target_file": "src/components/Button.tsx", "file_content": "..."}
```

This shows:
- **Tool name** - What tool the agent is using
- **Arguments** - What parameters the agent passed

### For Each Tool Response

```
Successfully wrote 532 characters to src/components/Button.tsx
```

This shows:
- **Result** - What happened when the tool executed
- **Details** - File path, size, or other relevant info

## Debugging with Logs

### Common Scenarios

#### 1. Agent Not Calling Tools

If you see Planner messages but no tool calls:
```
💬 Message 1/2 - From: Planner
   Here's my plan...

💬 Message 2/2 - From: Planner
   TASK_COMPLETED
```

**Issue**: Coder agent never executed. Termination happened too early.

**Solution**: Check termination conditions in orchestrator.py

#### 2. Tool Calls Failing

If you see tool calls but error responses:
```
🔧 TOOL CALL: write_file
   Arguments: {...}

Error: Permission denied
```

**Issue**: File system permissions or working directory issue

**Solution**: Check working directory is set correctly

#### 3. No Messages at All

If you see:
```
⚠️  No messages in result, using default response
```

**Issue**: Agent execution failed before producing messages

**Solution**: Check the error logs above for exceptions

## Customizing Logs

### Change Log Format

Edit `backend/app/main.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Simpler format
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
```

### Add File Logging

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agent_logs.log')  # Also log to file
    ]
)
```

### Change Verbosity

For more detailed output:
```python
logging.getLogger("autogen").setLevel(logging.DEBUG)  # Very verbose
```

For less output:
```python
logging.getLogger("app.services.chat_service").setLevel(logging.INFO)  # Less detail
```

## Benefits

1. **✅ See what agents are doing** - Real-time visibility into agent behavior
2. **✅ Debug tool calls** - See exactly which tools are called and with what arguments
3. **✅ Track conversation flow** - See how Planner and Coder collaborate
4. **✅ Identify errors quickly** - Full error traces with context
5. **✅ Understand agent decisions** - See the reasoning in agent messages
6. **✅ Verify file operations** - Confirm files are created/edited correctly

## Next Steps

With logging enabled, you can now:

1. **Run the backend**: `python backend/run.py`
2. **Create a project** through the frontend
3. **Send a chat message** like "Create a Button component"
4. **Watch the logs** to see exactly what the agents do
5. **Debug any issues** using the detailed log output

The logs will show you the complete conversation between agents, all tool calls, and the results - giving you full visibility into the multi-agent system!
