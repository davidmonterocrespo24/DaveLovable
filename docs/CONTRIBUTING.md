# Contributing to DaveLovable

Thank you for your interest in contributing to DaveLovable! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and considerate in all interactions
- Use welcoming and inclusive language
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

---

## Getting Started

### Prerequisites

- **Node.js:** 18+ (for frontend)
- **Python:** 3.8+ (for backend)
- **Git:** Latest version
- **Google AI API Key:** Get from [Google AI Studio](https://aistudio.google.com/apikey)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/DaveLovable.git
   cd DaveLovable
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/davidmonterocrespo24/DaveLovable.git
   ```

---

## Development Setup

### Backend Setup

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
# Edit .env and add your GOOGLE_API_KEY

# Initialize database
python init_db.py

# Run backend
python run.py
```

The backend runs on `http://localhost:8000` with API docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd front

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend runs on `http://localhost:8080`.

---

## Making Changes

### Branch Naming Convention

Create a branch for your work with a descriptive name:

- `feature/` - For new features (e.g., `feature/add-dark-mode`)
- `fix/` - For bug fixes (e.g., `fix/chat-scroll-issue`)
- `docs/` - For documentation changes (e.g., `docs/update-readme`)
- `refactor/` - For code refactoring (e.g., `refactor/api-structure`)

```bash
git checkout -b feature/your-feature-name
```

### Keeping Your Fork Updated

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

---

## Coding Standards

### General Guidelines

- **Language:** All code, comments, variable names, and documentation must be in **English only**
- **No Spanish or other languages** in the codebase
- Keep functions small and focused
- Use meaningful variable and function names
- Write self-documenting code

### Frontend (TypeScript/React)

- Use TypeScript for all new code
- Follow the existing code style
- Use functional components with hooks
- Use the `@/` alias for imports from `src/`
- Use shadcn/ui components where applicable

**Example:**
```typescript
// Good
import { Button } from "@/components/ui/button";
import { useProjects } from "@/hooks/useProjects";

const ProjectList: React.FC = () => {
  const { projects, isLoading } = useProjects();
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  return (
    <div className="grid gap-4">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
};
```

### Backend (Python/FastAPI)

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Use async/await for I/O operations
- Keep API endpoints RESTful

**Example:**
```python
# Good
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import Project, ProjectCreate
from app.services import ProjectService

router = APIRouter()

@router.post("", response_model=Project, status_code=201)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
) -> Project:
    """Create a new project."""
    return ProjectService.create_project(db, project, user_id=1)
```

### CSS/Styling

- Use Tailwind CSS utility classes
- Avoid custom CSS when Tailwind can achieve the same result
- Use the design system tokens defined in `tailwind.config.ts`

---

## Project Structure

### Backend Structure

```
backend/
├── app/
│   ├── agents/          # AI agent orchestration
│   ├── api/             # FastAPI endpoints
│   ├── core/            # Configuration, security
│   ├── db/              # Database connection
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── main.py          # FastAPI application
├── projects/            # Physical file storage
├── tests/               # Test files
└── requirements.txt     # Python dependencies
```

### Frontend Structure

```
front/
├── src/
│   ├── components/      # React components
│   │   ├── editor/      # Editor-specific components
│   │   └── ui/          # shadcn/ui components
│   ├── hooks/           # React Query hooks
│   ├── lib/             # Utility functions
│   ├── pages/           # Page components
│   └── services/        # API service layer
├── public/              # Static assets
└── package.json         # npm dependencies
```

---

## Testing

### Backend Testing

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_projects.py
```

### Frontend Testing

```bash
cd front

# Run linting
npm run lint

# Build to check for errors
npm run build
```

### Writing Tests

- Write tests for all new features
- Maintain or improve existing test coverage
- Use descriptive test names that explain the expected behavior

**Example:**
```python
# backend/tests/test_projects.py
def test_create_project_success(client, db_session):
    """Test that a project can be created successfully."""
    response = client.post("/api/v1/projects", json={
        "name": "Test Project",
        "description": "A test project"
    })
    
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"
```

---

## Pull Request Process

### Before Submitting

1. **Ensure your code follows the coding standards**
2. **Write/update tests** for your changes
3. **Update documentation** if needed
4. **Run tests locally** to ensure they pass
5. **Rebase your branch** on the latest main

### PR Guidelines

1. **Create a descriptive PR title** following conventional commits:
   - `feat: Add dark mode support`
   - `fix: Resolve chat scrolling issue`
   - `docs: Update API documentation`

2. **Write a clear PR description** including:
   - What changes were made
   - Why the changes were necessary
   - How to test the changes
   - Screenshots (for UI changes)

3. **Link related issues** using keywords:
   - `Closes #123`
   - `Fixes #456`

### Review Process

1. A maintainer will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR

---

## Issue Guidelines

### Reporting Bugs

When reporting a bug, please include:

1. **Description:** Clear description of the bug
2. **Steps to reproduce:** Numbered steps to reproduce the issue
3. **Expected behavior:** What should happen
4. **Actual behavior:** What actually happens
5. **Environment:** OS, browser, Node/Python versions
6. **Screenshots/Logs:** If applicable

**Example:**
```markdown
## Bug Description
The chat panel doesn't scroll to the latest message automatically.

## Steps to Reproduce
1. Open the editor for any project
2. Send a message in the chat panel
3. Send multiple messages until the panel should scroll

## Expected Behavior
The chat panel should auto-scroll to show the latest message.

## Actual Behavior
The latest messages are hidden below the visible area.

## Environment
- OS: macOS 14.0
- Browser: Chrome 120
- Node: 20.10.0
```

### Feature Requests

When requesting a feature:

1. **Description:** Clear description of the feature
2. **Use case:** Why this feature would be useful
3. **Proposed solution:** How you think it could work
4. **Alternatives:** Other solutions you've considered

---

## Development Tips

### Hot Reload

Both frontend and backend support hot reload during development:
- Frontend: Changes reflect immediately in the browser
- Backend: FastAPI reloads on file changes with `--reload`

### API Documentation

Access interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Debugging

**Backend:**
```python
# Add to your code for debugging
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message here")
```

**Frontend:**
```typescript
// Use React DevTools and browser console
console.log("Debug:", data);
```

### Database

The project uses SQLite by default. The database file is at `backend/davelovable.db`.

To reset the database:
```bash
cd backend
rm davelovable.db
python init_db.py
```

---

## Questions?

If you have questions about contributing:

1. Check existing issues and discussions
2. Open a new issue with the `question` label
3. Join our community discussions

Thank you for contributing to DaveLovable! 🚀
