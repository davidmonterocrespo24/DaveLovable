# Development Guide

This guide covers the development workflow for DaveLovable, including setup, common tasks, and best practices.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Common Development Tasks](#common-development-tasks)
- [Debugging](#debugging)
- [Testing](#testing)
- [Best Practices](#best-practices)

---

## Quick Start

### Prerequisites

- **Node.js:** 18+ 
- **Python:** 3.8+
- **Git:** Latest version
- **Google AI API Key:** [Get from Google AI Studio](https://aistudio.google.com/apikey)

### One-Command Setup

```bash
# Clone repository
git clone https://github.com/davidmonterocrespo24/DaveLovable.git
cd DaveLovable

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY
python init_db.py

# Frontend setup (new terminal)
cd front
npm install
```

### Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd front
npm run dev
```

Access the application at `http://localhost:8080`

---

## Development Environment

### Recommended IDE Setup

**VS Code Extensions:**
- ESLint
- Prettier
- Python
- Pylance
- Tailwind CSS IntelliSense
- TypeScript Vue Plugin (Volar)

### Environment Configuration

**Backend (.env):**
```env
GOOGLE_API_KEY=your_api_key
DEBUG=True
DATABASE_URL=sqlite:///./davelovable.db
```

**Frontend (.env):**
```env
VITE_API_URL=http://localhost:8000
```

---

## Running the Application

### Backend Server

```bash
cd backend
source venv/bin/activate

# Development mode (with hot reload)
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Available at:**
- API: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Server

```bash
cd front

# Development mode (with HMR)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Available at:**
- Frontend: `http://localhost:8080`

---

## Project Structure

### Backend Structure

```
backend/
├── app/
│   ├── agents/              # AI agent system
│   │   ├── orchestrator.py  # Agent orchestration
│   │   ├── config.py        # Agent configuration
│   │   └── tools/           # Agent tools (40+)
│   ├── api/                 # FastAPI endpoints
│   │   ├── projects.py      # Project CRUD
│   │   └── chat.py          # Chat/AI endpoints
│   ├── core/                # App configuration
│   │   ├── config.py        # Settings
│   │   └── gemini_client.py # Gemini API client
│   ├── db/                  # Database
│   │   └── database.py      # DB connection
│   ├── models/              # SQLAlchemy models
│   │   ├── project.py       # Project model
│   │   ├── chat.py          # Chat models
│   │   └── user.py          # User model
│   ├── schemas/             # Pydantic schemas
│   │   ├── project.py       # Project schemas
│   │   └── chat.py          # Chat schemas
│   ├── services/            # Business logic
│   │   ├── project_service.py
│   │   ├── chat_service.py
│   │   ├── filesystem_service.py
│   │   └── git_service.py
│   └── main.py              # FastAPI app
├── projects/                # Project file storage
├── tests/                   # Test files
├── requirements.txt         # Dependencies
├── init_db.py              # DB initialization
└── run.py                  # Server runner
```

### Frontend Structure

```
front/
├── src/
│   ├── components/          # React components
│   │   ├── editor/          # Editor components
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── CodeEditor.tsx
│   │   │   ├── FileExplorer.tsx
│   │   │   ├── PreviewPanelWithWebContainer.tsx
│   │   │   └── EditorTabs.tsx
│   │   └── ui/              # shadcn/ui components
│   ├── hooks/               # React Query hooks
│   │   ├── useProjects.ts
│   │   ├── useFiles.ts
│   │   └── useChat.ts
│   ├── lib/                 # Utilities
│   │   └── utils.ts
│   ├── pages/               # Page components
│   │   ├── Index.tsx        # Landing page
│   │   ├── Editor.tsx       # Main editor
│   │   └── NotFound.tsx     # 404 page
│   ├── services/            # API services
│   │   ├── api.ts           # REST API client
│   │   └── webcontainer.ts  # WebContainer service
│   ├── App.tsx              # Root component
│   └── main.tsx             # Entry point
├── public/                  # Static assets
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

---

## Common Development Tasks

### Adding a New API Endpoint

1. **Create schema** in `backend/app/schemas/`:
   ```python
   # backend/app/schemas/example.py
   from pydantic import BaseModel
   
   class ExampleCreate(BaseModel):
       name: str
       value: int
   
   class Example(ExampleCreate):
       id: int
       
       class Config:
           from_attributes = True
   ```

2. **Create service** in `backend/app/services/`:
   ```python
   # backend/app/services/example_service.py
   from sqlalchemy.orm import Session
   from app.schemas import Example, ExampleCreate
   
   class ExampleService:
       @staticmethod
       def create(db: Session, data: ExampleCreate) -> Example:
           # Business logic here
           pass
   ```

3. **Create endpoint** in `backend/app/api/`:
   ```python
   # backend/app/api/example.py
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from app.db import get_db
   from app.schemas import Example, ExampleCreate
   from app.services import ExampleService
   
   router = APIRouter()
   
   @router.post("", response_model=Example)
   def create_example(
       data: ExampleCreate,
       db: Session = Depends(get_db)
   ):
       return ExampleService.create(db, data)
   ```

4. **Register router** in `backend/app/main.py`:
   ```python
   from app.api.example import router as example_router
   app.include_router(example_router, prefix="/api/v1/example", tags=["Example"])
   ```

### Adding a New React Component

1. **Create component** in `front/src/components/`:
   ```typescript
   // front/src/components/MyComponent.tsx
   import { FC } from 'react';
   import { Button } from '@/components/ui/button';
   
   interface MyComponentProps {
     title: string;
     onClick: () => void;
   }
   
   export const MyComponent: FC<MyComponentProps> = ({ title, onClick }) => {
     return (
       <div className="p-4 border rounded-lg">
         <h2 className="text-xl font-bold">{title}</h2>
         <Button onClick={onClick}>Click me</Button>
       </div>
     );
   };
   ```

2. **Use the component:**
   ```typescript
   import { MyComponent } from '@/components/MyComponent';
   
   function Page() {
     return <MyComponent title="Hello" onClick={() => alert('Clicked!')} />;
   }
   ```

### Adding a New React Query Hook

```typescript
// front/src/hooks/useExample.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

export function useExamples() {
  return useQuery({
    queryKey: ['examples'],
    queryFn: () => api.get('/examples').then(res => res.data),
  });
}

export function useCreateExample() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: { name: string }) => 
      api.post('/examples', data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examples'] });
    },
  });
}
```

### Modifying Agent Tools

Agent tools are defined in `backend/app/agents/tools/`. To add a new tool:

1. **Create tool function:**
   ```python
   # backend/app/agents/tools/my_tool.py
   from autogen_core.tools import FunctionTool
   
   def my_tool_function(param1: str, param2: int) -> str:
       """
       Description of what the tool does.
       
       Args:
           param1: Description of param1
           param2: Description of param2
       
       Returns:
           Description of return value
       """
       # Tool implementation
       return f"Result: {param1} {param2}"
   
   my_tool = FunctionTool(
       func=my_tool_function,
       name="my_tool",
       description="Tool description for the agent"
   )
   ```

2. **Register tool** in orchestrator:
   ```python
   # backend/app/agents/orchestrator.py
   from app.agents.tools.my_tool import my_tool
   
   # Add to tools list
   coder_tools = [..., my_tool]
   ```

---

## Debugging

### Backend Debugging

**Logging:**
```python
import logging
logger = logging.getLogger(__name__)

# In your code
logger.info("Info message")
logger.debug("Debug message")
logger.error("Error message")
```

**Interactive debugger:**
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json
```

**VS Code launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Frontend Debugging

**React DevTools:**
- Install Chrome extension: React Developer Tools
- Inspect component hierarchy and state

**Console logging:**
```typescript
console.log('Data:', data);
console.table(arrayData);
console.dir(objectData);
```

**Network debugging:**
- Open Chrome DevTools → Network tab
- Filter by Fetch/XHR for API calls

### Agent Debugging

View agent interactions in real-time:
1. Use the streaming chat endpoint
2. Watch console output for tool calls
3. Check `agent_interactions` in chat responses

```python
# Enable verbose agent logging
import logging
logging.getLogger("autogen").setLevel(logging.DEBUG)
```

---

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_projects.py

# Run with coverage
pytest --cov=app

# Generate HTML coverage report
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd front

# Run linting
npm run lint

# Fix linting issues
npm run lint -- --fix

# Type checking
npx tsc --noEmit

# Build (catches errors)
npm run build
```

### Writing Tests

**Backend test example:**
```python
# backend/tests/test_projects.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_project():
    response = client.post("/api/v1/projects", json={
        "name": "Test Project",
        "description": "A test"
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"

def test_get_projects():
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## Best Practices

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Maximum line length: 120 characters
- Use async/await for I/O

**TypeScript:**
- Use TypeScript strict mode
- Define interfaces for props
- Use functional components
- Follow ESLint rules

### Git Workflow

1. Create feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. Push and create PR:
   ```bash
   git push origin feature/my-feature
   ```

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

### Error Handling

**Backend:**
```python
from fastapi import HTTPException

# Raise HTTP exceptions
if not project:
    raise HTTPException(status_code=404, detail="Project not found")

# Handle exceptions
try:
    result = risky_operation()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

**Frontend:**
```typescript
// Use try-catch
try {
  const data = await api.getProject(id);
} catch (error) {
  console.error('Failed to fetch project:', error);
  toast.error('Failed to load project');
}

// React Query error handling
const { data, error, isError } = useQuery(...);
if (isError) {
  return <ErrorMessage error={error} />;
}
```

### Performance

**Backend:**
- Use database indexes
- Implement pagination
- Cache expensive operations
- Use async operations

**Frontend:**
- Use React.memo for expensive components
- Implement lazy loading
- Use React Query caching
- Optimize images

---

## Useful Commands

### Database

```bash
# Reset database
cd backend
rm davelovable.db
python init_db.py

# View database (SQLite)
sqlite3 davelovable.db
.tables
SELECT * FROM projects;
.quit
```

### Dependencies

```bash
# Backend - add dependency
pip install package-name
pip freeze > requirements.txt

# Frontend - add dependency
npm install package-name
```

### Cleanup

```bash
# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove node_modules
rm -rf front/node_modules

# Remove build artifacts
rm -rf front/dist
```
