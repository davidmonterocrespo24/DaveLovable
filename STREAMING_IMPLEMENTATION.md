# Real-time Agent Interaction Streaming Implementation

## Overview

This implementation adds **Server-Sent Events (SSE)** streaming to display agent interactions in real-time as the multi-agent system (Planner + Coder) works on user requests.

## What Changed

### Backend Changes

#### 1. New Streaming Endpoint (`backend/app/api/chat.py`)

Added a new SSE streaming endpoint alongside the existing non-streaming endpoint:

- **New**: `POST /api/v1/chat/{project_id}/stream` - Streams events in real-time
- **Existing**: `POST /api/v1/chat/{project_id}` - Returns complete response (backward compatible)

The streaming endpoint uses FastAPI's `StreamingResponse` to send SSE events.

#### 2. Streaming Service Method (`backend/app/services/chat_service.py`)

Added `process_chat_message_stream()` method that:

- Uses `orchestrator.main_team.run_stream()` to get real-time agent events
- Yields SSE events as they occur:
  - `start` - Initial event with session info
  - `agent_interaction` - Agent thoughts, tool calls, and tool results
  - `complete` - Final response with message and code changes
  - `error` - Error events if something fails

### Frontend Changes

#### 1. API Service (`front/src/services/api.ts`)

Added `sendMessageStream()` method that:

- Uses `fetch()` with streaming response
- Reads SSE events using `ReadableStream`
- Parses `data:` lines and converts to JSON events
- Provides callbacks for each event type:
  - `onStart` - Session started
  - `onAgentInteraction` - New agent interaction
  - `onComplete` - Task completed
  - `onError` - Error occurred

#### 2. Chat Panel (`front/src/components/editor/ChatPanel.tsx`)

Updated to use streaming:

- Replaced `useSendChatMessage` hook with direct `chatApi.sendMessageStream()` call
- Replaced `sendMessageMutation.isPending` with `isStreaming` state
- Creates a placeholder message that updates in real-time
- Adds agent interactions to the message as they stream in
- Updates final content when complete

## Event Flow

```
User sends message
    ↓
[Frontend] Creates user message + placeholder assistant message
    ↓
[Frontend] Calls /chat/{id}/stream endpoint
    ↓
[Backend] Starts multi-agent execution with run_stream()
    ↓
[Backend] Yields "start" event → [Frontend] Updates session ID
    ↓
[Backend] Agent thinks → Yields "agent_interaction" (thought)
    ↓
[Frontend] Adds thought to message.agent_interactions array
    ↓
[Backend] Agent calls tool → Yields "agent_interaction" (tool_call)
    ↓
[Frontend] Adds tool call to message.agent_interactions array
    ↓
[Backend] Tool executes → Yields "agent_interaction" (tool_response)
    ↓
[Frontend] Adds tool result to message.agent_interactions array
    ↓
(repeat for multiple agent rounds)
    ↓
[Backend] Task completes → Yields "complete" event
    ↓
[Frontend] Updates message.content with final response
    ↓
Done! User sees all agent activity in real-time
```

## SSE Event Format

All events follow this structure:

```
data: {"type": "EVENT_TYPE", "data": {...}}

```

Example events:

```javascript
// Start event
data: {"type": "start", "data": {"session_id": 1, "user_message_id": 5}}

// Agent interaction - thought
data: {
  "type": "agent_interaction",
  "data": {
    "agent_name": "Planner",
    "message_type": "thought",
    "content": "I need to check the current file structure...",
    "tool_name": null,
    "tool_arguments": null,
    "timestamp": "2025-12-28T10:30:15.123Z"
  }
}

// Agent interaction - tool call
data: {
  "type": "agent_interaction",
  "data": {
    "agent_name": "Coder",
    "message_type": "tool_call",
    "content": "Calling: read_file",
    "tool_name": "read_file",
    "tool_arguments": {"filepath": "src/App.tsx"},
    "timestamp": "2025-12-28T10:30:16.456Z"
  }
}

// Agent interaction - tool response
data: {
  "type": "agent_interaction",
  "data": {
    "agent_name": "System",
    "message_type": "tool_response",
    "content": "import React from 'react'...",
    "tool_name": "read_file",
    "tool_arguments": null,
    "timestamp": "2025-12-28T10:30:16.789Z"
  }
}

// Complete event
data: {
  "type": "complete",
  "data": {
    "session_id": 1,
    "message": {
      "id": 10,
      "session_id": 1,
      "role": "assistant",
      "content": "I've updated the App.tsx file...",
      "agent_name": "Coder",
      "created_at": "2025-12-28T10:30:20.123Z"
    },
    "code_changes": []
  }
}

// Error event
data: {"type": "error", "data": {"message": "API key not configured"}}

```

## UI Display

The agent interactions are displayed in the `AgentInteraction` component (already implemented) which shows:

- **Thoughts** (💭): Agent reasoning and planning
- **Tool Calls** (🔧): What tools the agent is calling and with what arguments
- **Tool Responses** (✅): Results from tool executions

All interactions appear **in real-time** as they happen, not just when the task completes.

## Backward Compatibility

The original non-streaming endpoint (`POST /api/v1/chat/{project_id}`) still exists and works the same way. The streaming implementation is additive and doesn't break existing functionality.

## Testing

To test the streaming:

1. Start the backend: `python run.py` (or `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`)
2. Start the frontend: `npm run dev` (in the `front/` directory)
3. Open the editor and send a message to the AI
4. Watch the agent interactions appear in real-time as the agents work

You should see:
- "AI is thinking..." loading indicator
- Agent interactions streaming in one by one
- Final response appearing when complete
- All interactions preserved in the message history
