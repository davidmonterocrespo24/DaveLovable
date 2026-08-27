# Configuration Guide

This guide covers all configuration options for DaveLovable, including environment variables, application settings, and deployment configuration.

## Table of Contents

- [Backend Configuration](#backend-configuration)
- [Frontend Configuration](#frontend-configuration)
- [Agent Configuration](#agent-configuration)
- [Database Configuration](#database-configuration)
- [Security Configuration](#security-configuration)
- [WebContainers Configuration](#webcontainers-configuration)

---

## Backend Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory based on `.env.example`:

```bash
cd backend
cp .env.example .env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key for Gemini-3 Flash | `AIza...` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Generated | JWT secret key for token signing |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiration time |
| `DATABASE_URL` | `sqlite:///./davelovable.db` | Database connection string |
| `DEBUG` | `False` | Enable debug mode |
| `AUTOGEN_MAX_ROUND` | `20` | Maximum agent conversation rounds |

### Example .env File

```env
# Required: Google AI API Key (get from https://aistudio.google.com/apikey)
GOOGLE_API_KEY=your_google_api_key_here

# Optional: JWT Configuration (for future authentication)
SECRET_KEY=your_secret_key_here_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: Database (defaults to SQLite)
DATABASE_URL=sqlite:///./davelovable.db

# Optional: Debug mode
DEBUG=True

# Optional: AutoGen Configuration
AUTOGEN_MAX_ROUND=20
```

---

## Frontend Configuration

### Environment Variables

Create a `.env` file in the `front/` directory:

```bash
cd front
cp .env.example .env
```

### Available Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL |

### Example .env File

```env
# API URL for backend connection
VITE_API_URL=http://localhost:8000
```

### Production Build

For production builds, set the API URL:

```bash
VITE_API_URL=https://your-domain.com/api npm run build
```

---

## Agent Configuration

### Agent System Overview

DaveLovable uses a multi-agent system with two main agents:

1. **Planner Agent** - Creates strategic plans (no tools)
2. **Coder Agent** - Executes implementation using 40+ tools

### Agent Configuration File

Agent configurations are defined in `backend/app/agents/config.py`:

```python
# Model configuration
MODEL_NAME = "gemini-3-flash"

# Agent conversation limits
MAX_ROUNDS = 20

# Tool configurations
ENABLED_TOOLS = [
    "write_file",
    "edit_file", 
    "read_file",
    "delete_file",
    "list_dir",
    "git_commit",
    "run_terminal_cmd",
    # ... more tools
]
```

### Available Agent Tools

The Coder agent has access to 40+ tools:

**File Operations:**
- `read_file` - Read file content
- `write_file` - Create or overwrite files
- `edit_file` - Edit specific parts of files
- `delete_file` - Delete files

**Directory Operations:**
- `list_dir` - List directory contents
- `file_search` - Search for files by name
- `glob_search` - Search using glob patterns
- `grep_search` - Search file contents

**Git Operations:**
- `git_status` - Check repository status
- `git_add` - Stage files
- `git_commit` - Commit changes
- `git_diff` - View changes

**Terminal:**
- `run_terminal_cmd` - Execute shell commands

**Web Tools:**
- `web_search` - Search the web
- `wikipedia_search` - Search Wikipedia

---

## Database Configuration

### SQLite (Default)

By default, DaveLovable uses SQLite:

```env
DATABASE_URL=sqlite:///./davelovable.db
```

The database file is created at `backend/davelovable.db`.

### PostgreSQL (Production)

For production deployments, PostgreSQL is recommended:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/davelovable
```

**Setup PostgreSQL:**
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb davelovable

# Create user
sudo -u postgres createuser -P davelovable_user
```

### Database Initialization

Initialize or reset the database:

```bash
cd backend
source venv/bin/activate
python init_db.py
```

### Database Schema

The database stores:
- **Users** - User accounts (mock user for now)
- **Projects** - Project metadata
- **ProjectFiles** - File metadata (content stored on filesystem)
- **ChatSessions** - Chat conversation sessions
- **ChatMessages** - Individual chat messages

**Note:** File content is stored on the filesystem, not in the database.

---

## Security Configuration

### JWT Configuration

```env
SECRET_KEY=your_very_long_and_secure_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Important:** Always change `SECRET_KEY` in production!

### CORS Configuration

CORS settings are in `backend/app/core/config.py`:

```python
# Development (allow all origins)
CORS_ORIGINS = ["*"]

# Production (specify allowed origins)
CORS_ORIGINS = [
    "https://your-domain.com",
    "https://www.your-domain.com"
]
```

### API Rate Limiting

For production, configure rate limiting in Nginx:

```nginx
# In nginx configuration
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}
```

---

## WebContainers Configuration

### Required Headers

WebContainers require specific security headers. These are configured in `front/vite.config.ts`:

```typescript
server: {
  headers: {
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp"
  }
}
```

### Nginx Configuration

For production with Nginx:

```nginx
location / {
    # COOP/COEP headers for WebContainers
    add_header Cross-Origin-Opener-Policy same-origin;
    add_header Cross-Origin-Embedder-Policy require-corp;
    
    # Serve frontend files
    try_files $uri $uri/ /index.html;
}
```

### Browser Requirements

WebContainers work in:
- Chrome 89+
- Edge 89+
- Brave 1.22+

**Note:** Firefox and Safari are not fully supported.

---

## File Storage Configuration

### Project Directory

Projects are stored at:
```
backend/projects/project_{id}/
```

Each project includes:
- Git repository (`.git/`)
- Source files (`src/`)
- Configuration files (`package.json`, `vite.config.ts`, etc.)
- Agent state (`.agent_state.json`)

### Customizing Storage Location

To change the storage location, modify `backend/app/services/filesystem_service.py`:

```python
PROJECTS_DIR = Path("/custom/path/to/projects")
```

### Git Configuration

Each project is a Git repository. Configure Git globally:

```bash
git config --global user.name "DaveLovable AI"
git config --global user.email "ai@davelovable.local"
```

---

## Logging Configuration

### Backend Logging

Configure logging in `backend/app/main.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed debugging information |
| `INFO` | General operational information |
| `WARNING` | Warning messages |
| `ERROR` | Error messages |
| `CRITICAL` | Critical errors |

### Production Logging

For production, log to files:

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "/var/log/davelovable/app.log",
    maxBytes=10000000,
    backupCount=5
)
logging.getLogger().addHandler(handler)
```

---

## Performance Tuning

### Backend Workers

Configure uvicorn workers:

```bash
# Development (1 worker with reload)
uvicorn app.main:app --reload --workers 1

# Production (multiple workers)
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Nginx Caching

Add caching for static files:

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### Database Connection Pooling

For PostgreSQL with connection pooling:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/davelovable?pool_size=20&max_overflow=10
```

---

## Troubleshooting

### Common Issues

**1. Google API Key Not Working**
- Verify the key is correct
- Check API quotas in Google Cloud Console
- Ensure Gemini API is enabled

**2. Database Connection Failed**
- Check DATABASE_URL format
- Verify database exists
- Check user permissions

**3. WebContainers Not Loading**
- Verify COOP/COEP headers
- Use supported browser (Chrome/Edge)
- Check browser console for errors

**4. Port Already in Use**
```bash
# Find process using port
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### Debug Mode

Enable debug mode for more verbose output:

```env
DEBUG=True
```

This enables:
- Detailed error messages
- SQL query logging
- Agent interaction logging
