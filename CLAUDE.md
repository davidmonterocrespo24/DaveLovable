# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a lovable.dev clone - a web application that allows users to create web projects with AI assistance. The system consists of:

- **Frontend** (`/front`): React + TypeScript + Vite with visual code editor
- **Backend** (`/backend`): FastAPI + SQLite + Microsoft AutoGen for AI agent orchestration

The project is currently in development with frontend and backend built separately. They are **not yet connected** - the frontend is UI-only, and API integration is pending.

## Development Commands

### Frontend (in `/front` directory)

```bash
# Install dependencies
npm install

# Run development server (runs on http://localhost:8080)
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Backend (in `/backend` directory)

**Initial setup:**
```bash
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
```

**Running the backend:**
```bash
# Using the run script
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs on http://localhost:8000 with API documentation at http://localhost:8000/docs

## Architecture

### Backend Multi-Agent System

The backend uses **Microsoft AutoGen** to orchestrate four specialized AI agents that collaborate to generate code:

1. **Architect** - Plans system structure and component architecture
2. **UI Designer** - Designs visual interfaces using Tailwind CSS
3. **Coding Agent** - Generates TypeScript/React code
4. **Code Reviewer** - Reviews code for quality, bugs, and improvements

These agents communicate in a group chat (round-robin) via the `AgentOrchestrator` class in [backend/app/agents/orchestrator.py](backend/app/agents/orchestrator.py).

**Key methods:**
- `generate_code(user_request, context)` - Collaborative multi-agent code generation
- `quick_code_generation(user_request, agent_type)` - Single agent generation
- `review_code(code, context)` - Code review functionality

### Backend Architecture Pattern

The backend follows a layered architecture:

```
API Layer (FastAPI endpoints in /api)
    ↓
Service Layer (Business logic in /services)
    ↓
    ├→ Database (SQLAlchemy models in /models)
    └→ Agent Orchestrator (AutoGen agents in /agents)
```

**Key components:**
- [backend/app/api/projects.py](backend/app/api/projects.py) - Project and file CRUD endpoints
- [backend/app/api/chat.py](backend/app/api/chat.py) - AI chat endpoints
- [backend/app/services/project_service.py](backend/app/services/project_service.py) - Project management logic
- [backend/app/services/chat_service.py](backend/app/services/chat_service.py) - AI chat processing
- [backend/app/agents/orchestrator.py](backend/app/agents/orchestrator.py) - Agent orchestration (singleton pattern)

### Frontend Structure

The frontend uses a component-based architecture:

- **Pages** ([front/src/pages/](front/src/pages/)):
  - [Index.tsx](front/src/pages/Index.tsx) - Landing page
  - [Editor.tsx](front/src/pages/Editor.tsx) - Main editor interface
  - [NotFound.tsx](front/src/pages/NotFound.tsx) - 404 page

- **Editor Components** ([front/src/components/editor/](front/src/components/editor/)):
  - [ChatPanel.tsx](front/src/components/editor/ChatPanel.tsx) - AI chat interface
  - [CodeEditor.tsx](front/src/components/editor/CodeEditor.tsx) - Code editing with syntax highlighting
  - [FileExplorer.tsx](front/src/components/editor/FileExplorer.tsx) - File tree navigation
  - [PreviewPanel.tsx](front/src/components/editor/PreviewPanel.tsx) - Live preview (WebContainers pending)
  - [EditorTabs.tsx](front/src/components/editor/EditorTabs.tsx) - Multi-file tabs

- **UI Components** ([front/src/components/ui/](front/src/components/ui/)) - shadcn/ui components based on Radix UI

The frontend uses React Query for state management and react-resizable-panels for the layout.

### Database Schema

SQLite database with these main models (in [backend/app/models/](backend/app/models/)):

- **User** - User accounts (currently using MOCK_USER_ID = 1)
- **Project** - User projects with name, description, created_at
- **ProjectFile** - Individual code files with filename, filepath, content, language
- **ChatSession** - Chat sessions linked to projects
- **ChatMessage** - Individual messages with role (user/assistant) and content

## Important Context

### Authentication Status
- Backend has JWT and bcrypt setup ready but not fully implemented
- Frontend has no authentication yet
- Currently using `MOCK_USER_ID = 1` for all operations

### Frontend-Backend Connection
The frontend and backend are **FULLY INTEGRATED**. The integration includes:

1. **API Service Layer** - [front/src/services/api.ts](front/src/services/api.ts)
   - Complete REST API client for backend communication
   - Type-safe interfaces matching backend schemas

2. **React Query Hooks** - [front/src/hooks/](front/src/hooks/)
   - `useProjects()` - Project CRUD operations
   - `useFiles()` - File management
   - `useChat()` - AI chat integration

3. **Connected Components**:
   - ChatPanel - Sends messages to AI, displays responses
   - FileExplorer - Fetches and displays project files
   - CodeEditor - Shows real file content from backend

4. **Routing** - `/editor/:projectId` for multi-project support

See [README_INTEGRATION.md](README_INTEGRATION.md) and [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for details.

### Environment Variables
Backend requires `.env` file with:
- `OPENAI_API_KEY` - **Required** for AI agents to work
- `SECRET_KEY` - For JWT tokens
- `DATABASE_URL` - Defaults to SQLite
- `DEBUG` - Set to True for development

### Key Dependencies
- **Frontend**: React 18.3, TypeScript 5.8, Vite 5.4, Tailwind CSS 3.4, shadcn/ui, TanStack Query 5.83
- **Backend**: Python 3.8+, FastAPI 0.109, SQLAlchemy 2.0, pyautogen 0.2.18, OpenAI 1.10.0

## API Endpoints Reference

### Projects
- `POST /api/v1/projects` - Create project with initial files
- `GET /api/v1/projects` - List all projects for user
- `GET /api/v1/projects/{id}` - Get project with files
- `PUT /api/v1/projects/{id}` - Update project metadata
- `DELETE /api/v1/projects/{id}` - Delete project

### Files
- `GET /api/v1/projects/{id}/files` - List project files
- `POST /api/v1/projects/{id}/files` - Create new file
- `PUT /api/v1/projects/{id}/files/{file_id}` - Update file content
- `DELETE /api/v1/projects/{id}/files/{file_id}` - Delete file

### Chat
- `POST /api/v1/chat/{project_id}` - Send message, get AI response with code changes
- `GET /api/v1/chat/{project_id}/sessions` - List chat sessions
- `GET /api/v1/chat/{project_id}/sessions/{id}` - Get session with messages

## Working with AutoGen Agents

When modifying the AI agent system:

1. Agent system messages are defined in [backend/app/agents/config.py](backend/app/agents/config.py)
2. The orchestrator uses a singleton pattern - accessed via `get_orchestrator()`
3. Agents use `llm_config` which pulls from environment variable `OPENAI_API_KEY`
4. Group chat uses `AUTOGEN_MAX_ROUND` setting (default: 10 rounds)
5. Code extraction uses regex to find code blocks in agent responses

## File Aliases

Frontend uses `@/` alias for `front/src/` (configured in [front/vite.config.ts](front/vite.config.ts:14-16))

Example:
```typescript
import { Button } from "@/components/ui/button"
// Resolves to: front/src/components/ui/button
```

## Testing

Testing infrastructure is not yet implemented. When adding tests:
- Frontend: Consider Vitest (already using Vite)
- Backend: Use pytest with pytest-asyncio and httpx

## Code Standards

**CRITICAL: All code, comments, variable names, documentation, and commit messages MUST be written in English only.**

- Never use Spanish or any other language in code
- All comments must be in English
- All variable and function names must be in English
- All documentation and inline comments must be in English
- All commit messages must be in English

**NEVER create summary files** (e.g., SUMMARY.md, CHANGES.md, etc.) after completing work. Only create files that are explicitly requested or necessary for the project functionality.


All test on the test folder

Nunca toques el AGENT_SYSTEM_PROMPT , pero puedes modificar los otros