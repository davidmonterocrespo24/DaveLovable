# System Architecture

This document provides a comprehensive overview of DaveLovable's system architecture, including the multi-agent AI system, file storage strategy, and frontend-backend integration.

## Table of Contents

- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Multi-Agent System](#multi-agent-system)
- [File Storage System](#file-storage-system)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)

---

## Overview

DaveLovable is an AI-powered web development platform that enables users to create React applications through natural language conversations. The system consists of:

- **Frontend:** React + TypeScript + Vite with visual code editor
- **Backend:** FastAPI + SQLite + Microsoft AutoGen for AI orchestration
- **Preview:** WebContainers for browser-based Node.js execution
- **AI:** Google Gemini-3 Flash with multi-agent orchestration

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 USER                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                     React + TypeScript + Vite                                │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │ Landing     │  │   Editor    │  │ Visual      │  │ WebContainer        ││
│  │ Page        │  │   (Monaco)  │  │ Editor      │  │ Preview             ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    React Query + API Service Layer                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                          REST API / SSE
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                         │
│                    FastAPI + SQLAlchemy + AutoGen                           │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │     API Layer       │  │   Service Layer     │  │   Agent System      │ │
│  │                     │  │                     │  │                     │ │
│  │  - Projects API     │  │  - ProjectService   │  │  - Planner Agent    │ │
│  │  - Chat API         │  │  - ChatService      │  │  - Coder Agent      │ │
│  │  - Files API        │  │  - FileSystem       │  │  - 40+ Tools        │ │
│  │  - Git API          │  │  - GitService       │  │                     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   SQLite Database   │  │   File System       │  │   Gemini-3 Flash    │ │
│  │                     │  │                     │  │                     │ │
│  │  - Metadata only    │  │  - Project files    │  │  - 1M input tokens  │ │
│  │  - Sessions         │  │  - Git repos        │  │  - 64K output       │ │
│  │  - Messages         │  │  - Agent state      │  │                     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### Layered Architecture

The backend follows a clean layered architecture:

```
┌─────────────────────────────────────────┐
│           API Layer (FastAPI)           │
│  - HTTP endpoints                       │
│  - Request/Response validation          │
│  - Authentication (future)              │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           Service Layer                 │
│  - Business logic                       │
│  - Orchestrates operations              │
│  - Transaction management               │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────────┐   ┌───────────────────┐
│   Data Layer      │   │   Agent Layer     │
│  - SQLAlchemy     │   │  - AutoGen        │
│  - FileSystem     │   │  - Tool execution │
│  - Git            │   │  - LLM calls      │
└───────────────────┘   └───────────────────┘
```

### Component Details

#### API Layer (`backend/app/api/`)

Handles HTTP requests and responses:

| File | Purpose |
|------|---------|
| `projects.py` | Project CRUD, file management, Git operations |
| `chat.py` | AI chat, streaming, session management |

#### Service Layer (`backend/app/services/`)

Contains business logic:

| Service | Purpose |
|---------|---------|
| `ProjectService` | Project lifecycle management |
| `ChatService` | Chat processing, AI orchestration |
| `FileSystemService` | File operations, project scaffolding |
| `GitService` | Git operations, version control |

#### Models (`backend/app/models/`)

SQLAlchemy ORM models:

| Model | Purpose |
|-------|---------|
| `User` | User accounts (mock user for now) |
| `Project` | Project metadata |
| `ChatSession` | Chat conversation sessions |
| `ChatMessage` | Individual messages |

#### Schemas (`backend/app/schemas/`)

Pydantic validation schemas for request/response.

---

## Frontend Architecture

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         App.tsx                                  │
│                     (Router, Providers)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │ Index.tsx  │  │ Editor.tsx │  │ NotFound   │
       │ (Landing)  │  │ (Main)     │  │ (404)      │
       └────────────┘  └────────────┘  └────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │ ChatPanel  │  │ CodeEditor │  │ Preview    │
       │            │  │ (Monaco)   │  │ (WebCont.) │
       └────────────┘  └────────────┘  └────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │ FileTree   │  │ EditorTabs │  │ VisualEdit │
       └────────────┘  └────────────┘  └────────────┘
```

### State Management

**React Query** handles server state:

```typescript
// Queries (read)
useProjects()    // List projects
useProject(id)   // Single project with files
useFiles(id)     // Project files
useChatSessions(id) // Chat sessions

// Mutations (write)
useCreateProject()
useUpdateFile()
useSendMessage()
```

### Services

| Service | Purpose |
|---------|---------|
| `api.ts` | REST API client with axios |
| `webcontainer.ts` | WebContainer lifecycle management |

---

## Multi-Agent System

### Agent Architecture

DaveLovable uses Microsoft AutoGen with a SelectorGroupChat pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SelectorGroupChat                             │
│                   (Smart Agent Router)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       ┌────────────────┐            ┌────────────────┐
       │ Planner Agent  │            │  Coder Agent   │
       │                │            │                │
       │ - Strategy     │───────────▶│ - Execution    │
       │ - Planning     │            │ - 40+ Tools    │
       │ - No tools     │            │ - File ops     │
       └────────────────┘            └────────────────┘
                                            │
                              ┌─────────────┼─────────────┐
                              ▼             ▼             ▼
                       ┌──────────┐  ┌──────────┐  ┌──────────┐
                       │   File   │  │   Git    │  │ Terminal │
                       │  Tools   │  │  Tools   │  │  Tools   │
                       └──────────┘  └──────────┘  └──────────┘
```

### Agent Routing

The SelectorGroupChat intelligently routes requests:

| Request Type | Routing | Reason |
|--------------|---------|--------|
| `[VISUAL EDIT]` | Direct to Coder | Simple style changes |
| `[BUG FIX]` | Direct to Coder | Direct fix needed |
| Complex feature | Planner → Coder | Needs planning first |
| New component | Planner → Coder | Architecture decision |

### Tool Categories

**File Operations (8 tools):**
- `read_file`, `write_file`, `edit_file`, `delete_file`
- `list_dir`, `file_search`, `glob_search`, `grep_search`

**Git Operations (10 tools):**
- `git_status`, `git_add`, `git_commit`, `git_diff`
- `git_log`, `git_branch`, `git_checkout`, etc.

**Terminal Operations (1 tool):**
- `run_terminal_cmd` - Execute shell commands

**Data Operations (4 tools):**
- `read_json`, `write_json`, `read_csv`, `write_csv`

**Web Operations (2 tools):**
- `web_search`, `wikipedia_search`

### Conversation Flow

```
User: "Create a login form"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ SelectorGroupChat: Complex task → Route to Planner              │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Planner: "I'll plan the login form implementation..."           │
│          "1. Create LoginForm component"                        │
│          "2. Add form fields (email, password)"                 │
│          "3. Add validation and styling"                        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Coder: [Executes tools]                                         │
│        - write_file("src/components/LoginForm.tsx", "...")      │
│        - edit_file("src/App.tsx", add import)                   │
│        - git_commit("Add login form component")                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Response: "I've created a login form component with..."         │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Storage System

### Hybrid Storage Strategy

DaveLovable uses a hybrid storage approach:

```
┌─────────────────────────────────────────────────────────────────┐
│                      SQLite Database                             │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  Projects  │  │  Sessions  │  │  Messages  │                │
│  │  metadata  │  │  metadata  │  │  content   │                │
│  └────────────┘  └────────────┘  └────────────┘                │
│                                                                  │
│  NOTE: File CONTENT is NOT stored in database                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Physical File System                           │
│                                                                  │
│  backend/projects/                                               │
│  └── project_{id}/                                               │
│      ├── .git/                    # Git repository              │
│      ├── .gitignore                                             │
│      ├── .agent_state.json        # Agent memory                │
│      ├── package.json             # Dependencies                │
│      ├── vite.config.ts           # Vite config                 │
│      ├── tsconfig.json            # TypeScript config           │
│      ├── tailwind.config.js       # Tailwind config             │
│      ├── index.html               # Entry HTML                  │
│      └── src/                     # Source files                │
│          ├── main.tsx                                           │
│          ├── App.tsx                                            │
│          ├── index.css                                          │
│          └── components/          # Generated components        │
└─────────────────────────────────────────────────────────────────┘
```

### Why Hybrid Storage?

| Aspect | Database | Filesystem |
|--------|----------|------------|
| Project metadata | ✅ | ❌ |
| Chat messages | ✅ | ❌ |
| File content | ❌ | ✅ |
| Git history | ❌ | ✅ |
| Agent state | ❌ | ✅ |

**Benefits:**
- Git integration for version control
- Files ready for WebContainers
- Reduced database size
- Easy backup and restore

---

## Data Flow

### Project Creation Flow

```
User clicks "New Project"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: POST /api/v1/projects/from-message                    │
│           { message: "Create a landing page" }                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend: Gemini generates name/description                      │
│          ProjectService.create_project()                        │
│          FileSystemService.create_project_structure()           │
│          GitService.init_repository()                           │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Files created on disk:                                          │
│ - package.json, vite.config.ts, tsconfig.json                   │
│ - src/main.tsx, src/App.tsx, src/index.css                     │
│ - Initial git commit                                            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: Navigate to /editor/{projectId}                       │
│           Load files, initialize WebContainer                   │
└─────────────────────────────────────────────────────────────────┘
```

### Chat Message Flow (Streaming)

```
User types: "Add a contact form"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: POST /api/v1/chat/{projectId}/stream                  │
│           Connect to Server-Sent Events                         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend: ChatService.process_chat_message_stream()              │
│          - Change working directory to project                  │
│          - Run orchestrator.main_team.run(task)                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ (SSE Events)
┌─────────────────────────────────────────────────────────────────┐
│ Event: { type: "agent_thought", agent: "Planner", ... }         │
│ Event: { type: "tool_call", tool: "write_file", ... }           │
│ Event: { type: "tool_response", result: "Success", ... }        │
│ Event: { type: "final_response", content: "I created...", ... } │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: Update UI in real-time                                │
│           - Show agent interactions                             │
│           - Refresh file tree                                   │
│           - Reload WebContainer files                           │
└─────────────────────────────────────────────────────────────────┘
```

### WebContainer Preview Flow

```
Files changed via AI or editor
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: Fetch updated bundle                                  │
│           GET /api/v1/projects/{id}/bundle                      │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ WebContainer: Update file system                                │
│               await wc.fs.writeFile(path, content)              │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Vite HMR: Detect changes                                        │
│           Hot-reload affected modules                           │
│           Update preview without full reload                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Current Security Measures

| Layer | Measure |
|-------|---------|
| API | Input validation via Pydantic |
| Database | Parameterized queries (SQLAlchemy) |
| Files | Path sanitization |
| CORS | Configurable origins |

### Authentication (Planned)

```
┌─────────────────────────────────────────────────────────────────┐
│ Authentication Flow (Future)                                     │
│                                                                  │
│  User ──▶ Login ──▶ JWT Token ──▶ Protected Endpoints           │
│                                                                  │
│  Currently: Mock user (MOCK_USER_ID = 1)                        │
└─────────────────────────────────────────────────────────────────┘
```

### WebContainer Security

- Runs in browser sandbox
- No access to host system
- Network restricted to localhost
- COOP/COEP headers required

---

## Scalability Considerations

### Current Limitations

| Component | Limitation |
|-----------|------------|
| Database | SQLite (single-writer) |
| File Storage | Local filesystem |
| WebContainers | Client-side (scales naturally) |
| AI Calls | API rate limits |

### Scaling Strategy

For production scaling:

1. **Database:** Migrate to PostgreSQL
2. **File Storage:** Use S3/GCS with signed URLs
3. **Backend:** Multiple workers behind load balancer
4. **Caching:** Redis for session and API caching
5. **AI:** Request queuing and rate limiting

---

## Technology Stack Summary

### Backend

| Technology | Purpose |
|------------|---------|
| Python 3.8+ | Runtime |
| FastAPI | Web framework |
| SQLAlchemy | ORM |
| SQLite | Database |
| AutoGen | Agent orchestration |
| Gemini-3 Flash | LLM |

### Frontend

| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript | Language |
| Vite | Build tool |
| Tailwind CSS | Styling |
| shadcn/ui | Components |
| React Query | State management |
| Monaco Editor | Code editing |
| WebContainers | Preview execution |
