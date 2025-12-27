# Frontend-Backend Integration Guide

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Initialize database
python init_db.py

# Run backend
python run.py
```

Backend will run on http://localhost:8000

### 2. Frontend Setup

```bash
cd front

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# The default API_URL is http://localhost:8000/api/v1

# Run frontend
npm run dev
```

Frontend will run on http://localhost:8080

## Integration Changes Made

### 1. API Service Layer (`front/src/services/api.ts`)
- Complete REST API client for backend communication
- Type-safe interfaces matching backend schemas
- Error handling with custom ApiError class
- Endpoints for projects, files, and chat

### 2. React Query Hooks

#### `front/src/hooks/useProjects.ts`
- `useProjects()` - Fetch all projects
- `useProject(projectId)` - Fetch single project with files
- `useCreateProject()` - Create new project
- `useUpdateProject()` - Update project
- `useDeleteProject()` - Delete project

#### `front/src/hooks/useFiles.ts`
- `useFiles(projectId)` - Fetch files for a project
- `useCreateFile()` - Create new file
- `useUpdateFile()` - Update file content
- `useDeleteFile()` - Delete file

#### `front/src/hooks/useChat.ts`
- `useChatSessions(projectId)` - Fetch chat sessions
- `useChatSession(projectId, sessionId)` - Fetch specific session
- `useSendChatMessage()` - Send message to AI
- `useDeleteChatSession()` - Delete session

### 3. Component Updates

#### ChatPanel
- Now accepts `projectId`, `sessionId`, `onCodeChange` props
- Integrates with backend via `useSendChatMessage()` hook
- Loads previous messages from session
- Handles AI responses and code changes
- Shows loading state during AI processing

#### FileExplorer
- Now accepts `projectId` prop
- Fetches real files from backend via `useFiles()` hook
- Builds file tree from flat file list
- Shows loading state while fetching files
- Passes full file object (id, name, content) when file is selected

#### CodeEditor
- Now accepts file object with `{name, id, content}` instead of just filename
- Displays real file content from backend
- Prepared for future edit functionality

### 4. Routing Updates

Changed from `/editor` to `/editor/:projectId` to support multiple projects.

## Using the Integrated App

### Create a Project (via API)

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Project",
    "description": "A test project"
  }'
```

This returns a project with ID. Note the ID.

### Access the Editor

Navigate to `http://localhost:8080/editor/1` (replace 1 with your project ID)

### Chat with AI

1. Type a message in the chat panel (e.g., "Create a button component")
2. AI will process the request using AutoGen agents
3. Generated code will be saved to project files
4. Files will refresh automatically in the explorer

## Testing the Integration

### Manual Testing

1. **Backend Health Check**
   ```bash
   curl http://localhost:8000/docs
   ```
   Should open Swagger UI

2. **Create Project**
   ```bash
   curl -X POST http://localhost:8000/api/v1/projects \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Project"}'
   ```

3. **Open Editor**
   Navigate to http://localhost:8080/editor/1

4. **Send Chat Message**
   Type in chat: "Add a hello world component"
   Wait for AI response

5. **Check File Updates**
   Files should appear/update in the file explorer

### Automated Tests

See [backend/tests/README.md](backend/tests/README.md) and [front/tests/README.md](front/tests/README.md) for automated test instructions.

## Architecture Flow

```
User types message → ChatPanel
                        ↓
           useSendChatMessage() hook
                        ↓
        POST /api/v1/chat/{projectId}
                        ↓
            Backend ChatService
                        ↓
         AgentOrchestrator (AutoGen)
         ↓      ↓      ↓       ↓
    Architect UIDesigner CodingAgent CodeReviewer
                        ↓
            Generate code blocks
                        ↓
          Save to ProjectFile DB
                        ↓
           Return response + code_changes
                        ↓
          React Query invalidates cache
                        ↓
      FileExplorer refetches files
                        ↓
        User sees updated files
```

## Troubleshooting

### CORS Errors
- Ensure backend allows http://localhost:8080 in CORS settings
- Check `backend/app/main.py` CORS configuration

### API Connection Refused
- Verify backend is running on http://localhost:8000
- Check `.env` file in frontend has correct `VITE_API_URL`

### No Files Showing
- Verify project has files in database
- Check browser console for API errors
- Verify project ID in URL is correct

### AI Not Responding
- Verify `OPENAI_API_KEY` is set in backend `.env`
- Check backend logs for AutoGen errors
- Ensure OpenAI API key has credits

## Next Steps

1. Add real-time updates via WebSockets
2. Implement file editing in CodeEditor
3. Add WebContainers for live preview
4. Implement user authentication
5. Add collaborative features
