# API Reference

DaveLovable provides a comprehensive REST API for managing projects, files, chat sessions, and Git operations. The API is built with FastAPI and follows RESTful conventions.

## Base URL

```
http://localhost:8000/api/v1
```

API documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` (ReDoc).

---

## Authentication

> **Note:** Authentication is currently in development. All endpoints use a mock user ID (`MOCK_USER_ID = 1`) for now.

---

## Projects API

### Create Project

Creates a new project with a complete Vite + React + TypeScript + Tailwind CSS scaffold.

**Endpoint:** `POST /api/v1/projects`

**Request Body:**
```json
{
  "name": "My Project",
  "description": "A React application",
  "template": "react-vite",
  "framework": "react"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "My Project",
  "description": "A React application",
  "status": "active",
  "owner_id": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "template": "react-vite",
  "framework": "react",
  "thumbnail": null
}
```

---

### Create Project from Message

Creates a project using AI to generate the name and description from a user message.

**Endpoint:** `POST /api/v1/projects/from-message`

**Request Body:**
```json
{
  "message": "Create a landing page for a SaaS product",
  "attachments": [
    {
      "type": "image",
      "mime_type": "image/png",
      "data": "base64_encoded_data",
      "name": "design.png"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "project": {
    "id": 1,
    "name": "SaaS Landing Page",
    "description": "A modern landing page for a SaaS product",
    "status": "active",
    "owner_id": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "initial_message": "Create a landing page for a SaaS product",
  "attachments": [...]
}
```

---

### List Projects

Returns all projects for the current user (lightweight, excludes thumbnails for performance).

**Endpoint:** `GET /api/v1/projects`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Number of projects to skip |
| `limit` | int | 100 | Maximum number of projects to return |

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "My Project",
    "description": "A React application",
    "status": "active",
    "owner_id": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "template": "react-vite",
    "framework": "react"
  }
]
```

---

### Get Project

Returns a specific project with all its files.

**Endpoint:** `GET /api/v1/projects/{project_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "My Project",
  "description": "A React application",
  "status": "active",
  "owner_id": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "template": "react-vite",
  "framework": "react",
  "thumbnail": null,
  "files": [
    {
      "id": 1,
      "project_id": 1,
      "filename": "App.tsx",
      "filepath": "src/App.tsx",
      "content": "...",
      "language": "typescript",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### Update Project

Updates project metadata.

**Endpoint:** `PUT /api/v1/projects/{project_id}`

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "status": "active"
}
```

**Response:** `200 OK`

---

### Delete Project

Deletes a project and all associated files.

**Endpoint:** `DELETE /api/v1/projects/{project_id}`

**Response:** `204 No Content`

---

### Get Project Thumbnail

Returns only the thumbnail for lazy loading optimization.

**Endpoint:** `GET /api/v1/projects/{project_id}/thumbnail`

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "thumbnail": "data:image/png;base64,..."
}
```

---

### Upload Project Thumbnail

Uploads a base64-encoded screenshot as the project thumbnail.

**Endpoint:** `POST /api/v1/projects/{project_id}/thumbnail/upload`

**Request Body:**
```json
{
  "thumbnail": "data:image/png;base64,..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Thumbnail uploaded successfully",
  "project_id": 1,
  "thumbnail_size": 12345
}
```

---

### Download Project

Downloads the project as a ZIP file.

**Endpoint:** `GET /api/v1/projects/{project_id}/download`

**Response:** ZIP file with `Content-Disposition: attachment`

---

## Files API

### List Project Files

Returns all files for a project (read from filesystem).

**Endpoint:** `GET /api/v1/projects/{project_id}/files`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "project_id": 1,
    "filename": "App.tsx",
    "filepath": "src/App.tsx",
    "content": "import React from 'react'...",
    "language": "typescript",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Create File

Adds a new file to the project.

**Endpoint:** `POST /api/v1/projects/{project_id}/files`

**Request Body:**
```json
{
  "filepath": "src/components/Button.tsx",
  "content": "import React from 'react'...",
  "language": "typescript"
}
```

**Response:** `201 Created`

---

### Update File

Updates a file's content.

**Endpoint:** `PUT /api/v1/projects/{project_id}/files/{file_id}`

**Request Body:**
```json
{
  "filepath": "src/components/Button.tsx",
  "content": "updated content...",
  "language": "typescript"
}
```

**Response:** `200 OK`

---

### Delete File

Deletes a file from the project.

**Endpoint:** `DELETE /api/v1/projects/{project_id}/files/{file_id}`

**Request Body:**
```json
{
  "filepath": "src/components/Button.tsx"
}
```

**Response:** `204 No Content`

---

### Get Project Bundle

Returns all files in WebContainers-compatible format.

**Endpoint:** `GET /api/v1/projects/{project_id}/bundle`

**Response:** `200 OK`
```json
{
  "files": {
    "src/App.tsx": "import React from 'react'...",
    "src/main.tsx": "import { createRoot }...",
    "package.json": "{ \"name\": \"project\"... }"
  }
}
```

---

## Visual Editor API

### Apply Visual Edit

Applies visual style changes directly to component files.

**Endpoint:** `POST /api/v1/projects/{project_id}/visual-edit`

**Request Body:**
```json
{
  "filepath": "src/App.tsx",
  "element_selector": "button",
  "style_changes": {
    "color": "#ffffff",
    "backgroundColor": "#3b82f6"
  },
  "class_name": "px-4 py-2 bg-blue-500 text-white rounded"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Visual edit applied successfully",
  "filepath": "src/App.tsx"
}
```

---

## Chat API

### Send Message (Streaming)

Sends a chat message and streams the AI response with real-time agent interactions.

**Endpoint:** `POST /api/v1/chat/{project_id}/stream`

**Request Body:**
```json
{
  "message": "Create a login form component",
  "session_id": 1,
  "attachments": [
    {
      "type": "image",
      "mime_type": "image/png",
      "data": "base64_encoded_data",
      "name": "design.png"
    }
  ]
}
```

**Response:** Server-Sent Events (SSE)

```
data: {"type": "agent_thought", "data": {"agent": "Planner", "content": "Analyzing request..."}}

data: {"type": "tool_call", "data": {"tool": "write_file", "arguments": {"path": "src/Login.tsx"}}}

data: {"type": "tool_response", "data": {"result": "File created successfully"}}

data: {"type": "final_response", "data": {"content": "I've created a login form..."}}
```

**Event Types:**
| Type | Description |
|------|-------------|
| `agent_thought` | Agent's reasoning/planning |
| `tool_call` | Tool being invoked |
| `tool_response` | Result of tool execution |
| `final_response` | Final assistant message |
| `error` | Error occurred |

---

### Send Message (Non-Streaming)

Sends a chat message and waits for complete response (backward compatible).

**Endpoint:** `POST /api/v1/chat/{project_id}`

**Request Body:**
```json
{
  "message": "Create a login form component",
  "session_id": 1
}
```

**Response:** `200 OK`
```json
{
  "session_id": 1,
  "message": {
    "id": 10,
    "session_id": 1,
    "role": "assistant",
    "content": "I've created a login form component...",
    "agent_name": "Coder",
    "created_at": "2024-01-15T10:35:00Z",
    "agent_interactions": [...]
  },
  "code_changes": [
    {
      "filepath": "src/components/Login.tsx",
      "action": "create"
    }
  ]
}
```

---

### Create Chat Session

Creates a new chat session for a project.

**Endpoint:** `POST /api/v1/chat/{project_id}/sessions`

**Request Body:**
```json
{
  "project_id": 1,
  "title": "New Chat"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "project_id": 1,
  "title": "New Chat",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### List Chat Sessions

Returns all chat sessions for a project.

**Endpoint:** `GET /api/v1/chat/{project_id}/sessions`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "project_id": 1,
    "title": "New Chat",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Get Chat Session

Returns a specific chat session with all messages.

**Endpoint:** `GET /api/v1/chat/{project_id}/sessions/{session_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "project_id": 1,
  "title": "New Chat",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "messages": [
    {
      "id": 1,
      "session_id": 1,
      "role": "user",
      "content": "Create a button component",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "session_id": 1,
      "role": "assistant",
      "content": "I've created a Button component...",
      "agent_name": "Coder",
      "created_at": "2024-01-15T10:30:30Z",
      "agent_interactions": [...]
    }
  ]
}
```

---

### Reconnect to Session

Reconnects to a session and retrieves new messages since a specific message ID.

**Endpoint:** `GET /api/v1/chat/{project_id}/sessions/{session_id}/reconnect`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `since_message_id` | int | 0 | Get messages after this ID |

**Response:** `200 OK`
```json
{
  "session_id": 1,
  "project_id": 1,
  "new_messages": [...],
  "total_messages": 10,
  "has_more": true
}
```

---

### Delete Chat Session

Deletes a chat session and all its messages.

**Endpoint:** `DELETE /api/v1/chat/{project_id}/sessions/{session_id}`

**Response:** `204 No Content`

---

## Git API

### Get Commit History

Returns Git commit history for a project.

**Endpoint:** `GET /api/v1/projects/{project_id}/git/history`

**Query Parameters:**
| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | int | 20 | 100 | Maximum commits to return |

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "commits": [
    {
      "hash": "abc123",
      "short_hash": "abc123",
      "author": "AI Agent",
      "email": "ai@davelovable.local",
      "date": "2024-01-15T10:30:00Z",
      "message": "Add login form component"
    }
  ],
  "total": 1
}
```

---

### Get Git Diff

Returns uncommitted changes.

**Endpoint:** `GET /api/v1/projects/{project_id}/git/diff`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `filepath` | string | Optional specific file to diff |

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "filepath": null,
  "diff": "diff --git a/src/App.tsx..."
}
```

---

### Get File at Commit

Returns file content at a specific commit.

**Endpoint:** `GET /api/v1/projects/{project_id}/git/file/{commit_hash}`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filepath` | string | Yes | File path to retrieve |

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "commit_hash": "abc123",
  "filepath": "src/App.tsx",
  "content": "import React from 'react'..."
}
```

---

### Restore to Commit

Restores the project to a specific commit (creates a new commit).

**Endpoint:** `POST /api/v1/projects/{project_id}/git/restore/{commit_hash}`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Restored to commit abc123",
  "project_id": 1,
  "commit_hash": "abc123def456..."
}
```

---

### Checkout Commit

Temporarily checkout a specific commit (detached HEAD state).

**Endpoint:** `POST /api/v1/projects/{project_id}/git/checkout/{commit_hash}`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Checked out commit abc123",
  "project_id": 1,
  "commit_hash": "abc123def456..."
}
```

---

### Checkout Branch

Returns to a branch from detached HEAD state.

**Endpoint:** `POST /api/v1/projects/{project_id}/git/checkout-branch`

**Request Body:**
```json
{
  "branch_name": "main"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Checked out branch main",
  "project_id": 1,
  "branch": "main"
}
```

---

### Get Current Branch

Returns the current branch or commit hash if in detached HEAD state.

**Endpoint:** `GET /api/v1/projects/{project_id}/git/branch`

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "branch": "main"
}
```

---

### Get Git Remote Config

Returns Git remote configuration.

**Endpoint:** `GET /api/v1/projects/{project_id}/git/config`

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "remote_url": "https://github.com/user/repo.git",
  "remote_name": "origin"
}
```

---

### Set Git Remote Config

Configures Git remote for a project.

**Endpoint:** `POST /api/v1/projects/{project_id}/git/config`

**Request Body:**
```json
{
  "remote_url": "https://github.com/user/repo.git",
  "remote_name": "origin"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Remote 'origin' configured successfully",
  "project_id": 1,
  "remote_name": "origin",
  "remote_url": "https://github.com/user/repo.git"
}
```

---

### Sync with Remote

Syncs project with remote repository (fetch, pull, commit, push).

**Endpoint:** `POST /api/v1/projects/{project_id}/git/sync`

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "success": true,
  "message": "Synced successfully"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Error message describing what went wrong"
}
```

### 404 Not Found
```json
{
  "detail": "Project not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, there is no rate limiting implemented. For production deployments, consider implementing rate limiting via Nginx or a reverse proxy.

---

## WebSocket Support

WebSocket support is not currently implemented. Real-time updates are provided via Server-Sent Events (SSE) through the streaming chat endpoint.

---

## CORS Configuration

The API allows all origins in development mode. For production, configure allowed origins in `backend/app/core/config.py`.
