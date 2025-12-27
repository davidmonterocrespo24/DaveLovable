# Quick Start Guide

Get the lovable.dev clone up and running in 5 minutes.

## Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API Key

## Step 1: Backend Setup (2 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here

# Initialize database (creates sample user)
python init_db.py

# Start backend
python run.py
```

✅ Backend running at http://localhost:8000

## Step 2: Frontend Setup (2 minutes)

```bash
# Open new terminal
cd front

# Install dependencies
npm install

# Create .env (optional, uses default)
cp .env.example .env

# Start frontend
npm run dev
```

✅ Frontend running at http://localhost:8080

## Step 3: Create Your First Project (1 minute)

```bash
# Create a project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My First App", "description": "Hello World"}'
```

You'll get a response like:
```json
{
  "id": 1,
  "name": "My First App",
  "description": "Hello World",
  "files": [...]
}
```

Note the `id` (likely 1 for your first project).

## Step 4: Open the Editor

Visit: http://localhost:8080/editor/1

(Replace `1` with your project ID)

## Step 5: Chat with AI

In the chat panel (left side), type:

```
Create a colorful button component with hover effects
```

Watch as:
1. AI agents collaborate to generate code
2. New Button.tsx file appears in file explorer
3. Code is automatically saved

## Step 6: Explore

- Click files in the explorer to view them
- Send more chat messages to modify code
- Watch the AI create and update files in real-time

## What's Happening Behind the Scenes?

```
You → ChatPanel → Backend API → AutoGen Agents
                                  ↓
            Architect + UI Designer + Coder + Reviewer
                                  ↓
                          Generated Code
                                  ↓
                         Saved to Database
                                  ↓
           Frontend Refetches → FileExplorer Updates
```

## Common Issues

### "Connection refused" or "Network error"

**Problem:** Backend not running

**Solution:**
```bash
cd backend
source venv/bin/activate
python run.py
```

### "No files showing"

**Problem:** Project not created or wrong ID

**Solution:**
```bash
# List all projects
curl http://localhost:8000/api/v1/projects

# Use correct project ID in URL
```

### "AI not responding"

**Problem:** OpenAI API key not set or invalid

**Solution:**
1. Check `backend/.env` has `OPENAI_API_KEY=sk-...`
2. Verify key is valid and has credits
3. Restart backend after changing .env

### Port already in use

**Problem:** Port 8000 or 8080 already taken

**Solution:**

For backend (change port in `backend/run.py`):
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use different port
```

For frontend (change port in `front/vite.config.ts`):
```typescript
server: {
  port: 8081,  // Use different port
}
```

## Next Steps

- Read [README_INTEGRATION.md](README_INTEGRATION.md) for architecture details
- Follow [TEST_PLAN.md](TEST_PLAN.md) to test all features
- Check [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for advanced usage

## Features to Try

1. **Create Multiple Files**
   - "Add a Header component"
   - "Create a Card component"
   - "Add a Footer"

2. **Modify Existing Files**
   - "Add a title prop to the Card component"
   - "Make the button larger"

3. **Complex Requests**
   - "Create a responsive navigation bar with mobile menu"
   - "Add a contact form with validation"

## Development Workflow

1. Start both backend and frontend
2. Create a project via API or Swagger UI (http://localhost:8000/docs)
3. Open editor with project ID
4. Chat with AI to generate/modify code
5. View changes in file explorer
6. Iterate!

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

Key endpoints:
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project with files
- `POST /api/v1/chat/{id}` - Send message to AI
- `GET /api/v1/projects/{id}/files` - List files

## Stopping the Services

**Backend:**
```bash
# Press Ctrl+C in backend terminal
```

**Frontend:**
```bash
# Press Ctrl+C in frontend terminal
```

## Database

SQLite database is stored at `backend/lovable_dev.db`. You can:

- View with: `sqlite3 backend/lovable_dev.db`
- Delete to reset: `rm backend/lovable_dev.db && python backend/init_db.py`

## Sample User

Default user created by `init_db.py`:
- Email: demo@lovable.dev
- Password: demo123
- ID: 1

(Authentication not yet implemented in frontend)

---

**You're all set!** 🚀

Happy coding with AI! Try asking the AI to build something interesting.
