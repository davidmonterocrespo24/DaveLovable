# Physical File System Implementation

## What Was Implemented

We've implemented a **dual storage system** that saves generated code both in the database and as physical files on disk. This enables **WebContainers** integration for running the preview entirely in the browser.

## Changes Made

### 1. Configuration (`backend/app/core/config.py`)

Added configuration for projects directory:
```python
PROJECTS_BASE_DIR: str = "./projects"
```

### 2. File System Service (`backend/app/services/filesystem_service.py`)

**NEW FILE** - Manages physical file operations:

**Key Methods:**
- `create_project_structure(project_id, name)` - Creates complete Vite + React + TypeScript project
- `write_file(project_id, filepath, content)` - Writes file to disk
- `read_file(project_id, filepath)` - Reads file from disk
- `delete_file(project_id, filepath)` - Deletes file
- `delete_project(project_id)` - Deletes entire project directory
- `get_all_files(project_id)` - Returns all files as list for WebContainers

**Initial Project Structure Created:**
```
backend/projects/project_X/
├── package.json           # Dependencies: React, Vite, TypeScript, Tailwind
├── vite.config.ts         # Vite configuration (port 3000)
├── tsconfig.json          # TypeScript strict mode config
├── tailwind.config.js     # Tailwind CSS config
├── postcss.config.js      # PostCSS with Tailwind + Autoprefixer
├── index.html             # HTML entry point
└── src/
    ├── main.tsx           # React entry point with StrictMode
    ├── App.tsx            # Default App component with welcome message
    ├── index.css          # Tailwind directives + base styles
    └── components/        # Directory for AI-generated components
```

### 3. Updated Project Service (`backend/app/services/project_service.py`)

**Modified Methods:**
- `create_project()` - Now calls `FileSystemService.create_project_structure()`
- `delete_project()` - Now calls `FileSystemService.delete_project()`
- `add_file_to_project()` - Now writes to filesystem after DB
- `update_file()` - Now updates filesystem after DB
- `delete_file()` - Now deletes from filesystem

**Sync Strategy:** All file operations sync to both DB and filesystem

### 4. Updated Chat Service (`backend/app/services/chat_service.py`)

When AI generates code:
- Files are saved to database
- Files are written to filesystem using `FileSystemService.write_file()`
- Path defaults to `src/components/{filename}` for new components

### 5. New API Endpoint (`backend/app/api/projects.py`)

**GET** `/api/v1/projects/{project_id}/bundle`

Returns all project files in WebContainers-compatible format:

```json
{
  "files": {
    "package.json": "{...}",
    "index.html": "<!DOCTYPE html>...",
    "src/main.tsx": "import React...",
    "src/components/Button.tsx": "export const Button..."
  }
}
```

### 6. Updated Frontend API Types (`front/src/services/api.ts`)

Fixed `SendChatMessageResponse` interface to match backend:
```typescript
export interface SendChatMessageResponse {
  message: {
    role: string;
    content: string;
    agent_name: string | null;
    message_metadata: string | null;
    id: number;
    session_id: number;
    created_at: string;
  };
  session_id: number;
  code_changes?: Array<{
    filename: string;
    content: string;
    language: string;
  }>;
}
```

### 7. Updated ChatPanel (`front/src/components/editor/ChatPanel.tsx`)

Changed from `response.response` to `response.message.content` to match backend response structure.

## How It Works

### Project Creation Flow

1. User creates project via API
2. Database record created in SQLite
3. `FileSystemService.create_project_structure()` called
4. Physical directory created at `backend/projects/project_{id}/`
5. Complete Vite + React project scaffolding written to disk
6. Initial files also saved to database

### AI Code Generation Flow

1. User sends chat message: "Create a Button component"
2. AutoGen CodingAgent generates React/TypeScript code
3. `ChatService.process_chat_message()` processes response
4. For each generated file:
   - Check if file exists in database
   - If exists: Update DB + Update filesystem
   - If new: Create in DB + Write to filesystem
5. Frontend receives `code_changes` array
6. React Query invalidates file list
7. FileExplorer refreshes to show new files

### Bundle Endpoint Flow

1. Frontend requests `/api/v1/projects/3/bundle`
2. Backend verifies project ownership
3. `FileSystemService.get_all_files()` reads all files from disk
4. Files converted to `{ "path": "content" }` dictionary
5. Returned as JSON for WebContainers to mount

## Testing Results

**Test: Create Project**
```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test WebContainers","description":"Testing","template":"react-vite"}'

# Response: Project ID 3 created
```

**Test: Verify Physical Files**
```bash
ls -la backend/projects/project_3/
# Output:
# index.html
# package.json
# postcss.config.js
# src/
# tailwind.config.js
# tsconfig.json
# vite.config.ts

ls -la backend/projects/project_3/src/
# Output:
# App.tsx
# components/
# index.css
# main.tsx
```

**Test: Bundle Endpoint**
```bash
curl http://localhost:8000/api/v1/projects/3/bundle

# Response: 9 files returned
# - index.html
# - package.json
# - postcss.config.js
# - src/App.tsx
# - src/index.css
# - src/main.tsx
# - tailwind.config.js
# - tsconfig.json
# - vite.config.ts
```

## File Paths

**Database Storage:**
- Files stored in `lovable_dev.db` SQLite database
- Table: `project_files`
- Fields: `id`, `project_id`, `filename`, `filepath`, `content`, `language`

**Filesystem Storage:**
- Base directory: `backend/projects/`
- Project directory: `backend/projects/project_{id}/`
- Example: `backend/projects/project_3/src/components/Button.tsx`

## Benefits

✅ **WebContainers Ready** - All files available for browser-based execution
✅ **No Build Step** - Files immediately available
✅ **Complete Projects** - Full Vite + React setup with dependencies
✅ **Database Queryable** - Fast file listing and searching
✅ **Filesystem Accessible** - Can serve files, run builds, etc.
✅ **Automatic Sync** - All operations keep DB and filesystem in sync

## Next Steps for WebContainers Integration

1. **Install WebContainers** in frontend:
   ```bash
   cd front
   npm install @webcontainer/api
   ```

2. **Create WebContainer Service** to:
   - Boot WebContainer instance
   - Fetch project bundle from `/api/v1/projects/{id}/bundle`
   - Mount files to WebContainer
   - Run `npm install`
   - Start dev server with `npm run dev`
   - Get server URL for preview iframe

3. **Update PreviewPanel** to:
   - Initialize WebContainer on mount
   - Load project files
   - Display preview iframe with WebContainer URL
   - Handle file updates for hot reload

4. **Add Controls** for:
   - Restart server
   - Clear cache
   - View console output
   - Install additional packages

See [WEBCONTAINERS_GUIDE.md](WEBCONTAINERS_GUIDE.md) for detailed integration steps.

## Files Modified

- `backend/app/core/config.py` - Added PROJECTS_BASE_DIR
- `backend/app/services/filesystem_service.py` - **NEW FILE**
- `backend/app/services/project_service.py` - Added filesystem sync
- `backend/app/services/chat_service.py` - Added filesystem writes
- `backend/app/api/projects.py` - Added /bundle endpoint
- `front/src/services/api.ts` - Fixed response types
- `front/src/components/editor/ChatPanel.tsx` - Fixed message access
- `CLAUDE.md` - Updated with file storage info
- `WEBCONTAINERS_GUIDE.md` - **NEW FILE**

## Summary

The system now maintains a **complete, executable Vite + React + TypeScript project** on disk for every project. When AI generates code, it's immediately written to the filesystem, making it ready for WebContainers to execute in the browser without any backend compute.
