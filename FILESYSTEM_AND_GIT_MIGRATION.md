# Migration to Filesystem + Git Architecture

## Overview

The project has been successfully migrated from a **database-centric** architecture to a **filesystem + Git** architecture for file storage and version control.

## What Changed

### Before (Database Storage)
- **File Content**: Stored in SQLite database (`project_files.content` column)
- **Version Control**: No version control
- **Metadata**: Stored in database
- **Problem**: Content duplicated (DB + filesystem), no version history

### After (Filesystem + Git)
- **File Content**: Stored only in physical filesystem (`backend/projects/project_{id}/`)
- **Version Control**: Git repository per project
- **Metadata**: Minimal metadata in database (filename, filepath, language, timestamps)
- **Benefits**: Single source of truth, full version history, standard Git workflow

## Architecture Changes

### Database Schema

**Removed:**
- `project_files.content` column (no longer stores file content)

**Kept:**
- `project_files.id`, `project_id`, `filename`, `filepath`, `language`, `created_at`, `updated_at`

The database now stores only **file metadata**, not content.

### File Storage

**Physical Structure:**
```
backend/projects/
  └── project_3/
      ├── .git/              # Git repository
      ├── .gitignore
      ├── package.json
      ├── vite.config.ts
      ├── tsconfig.json
      ├── tsconfig.node.json
      ├── index.html
      └── src/
          ├── App.tsx
          ├── main.tsx
          ├── index.css
          └── components/
              └── Card.tsx
```

Each project is a complete, self-contained Git repository.

### Version Control with Git

**Features:**
- ✅ Every project is a Git repository
- ✅ Initial commit on project creation
- ✅ Automatic commits on file changes
- ✅ Automatic commits on AI-generated code
- ✅ Full commit history
- ✅ Ability to restore previous versions

**Commit Messages:**
- `"Initial commit: Project scaffolding"` - On project creation
- `"Add file: src/components/Button.tsx"` - When adding new files
- `"Update file: src/App.tsx"` - When updating files
- `"Delete file: src/old.tsx"` - When deleting files
- `"AI generated code: Create a Button component"` - When AI generates code

## New Services

### GitService (`backend/app/services/git_service.py`)

Complete Git operations service:

**Methods:**
- `init_repository(project_id)` - Initialize Git repo for a project
- `commit_changes(project_id, message, files)` - Commit changes
- `get_commit_history(project_id, limit)` - Get commit log
- `get_file_at_commit(project_id, filepath, commit_hash)` - Get file at specific commit
- `get_diff(project_id, filepath)` - Get uncommitted changes
- `restore_commit(project_id, commit_hash)` - Restore to previous commit

**Usage Example:**
```python
from app.services.git_service import GitService

# Commit changes
GitService.commit_changes(
    project_id=3,
    message="Add new component",
    files=["src/components/Button.tsx"]
)

# Get history
commits = GitService.get_commit_history(project_id=3, limit=10)
```

### Updated FileSystemService

**Enhanced with:**
- Automatic Git init on `create_project_structure()`
- All file operations integrate with Git

### Updated ProjectService

**Changes:**
- `get_project_files()` - Now reads content from filesystem, returns list of dicts
- `add_file_to_project()` - Writes to filesystem + Git commit
- `update_file()` - Updates filesystem + Git commit
- `delete_file()` - Deletes from filesystem + Git commit
- `_create_initial_files()` - Only stores metadata in DB

### Updated ChatService

**Changes:**
- Reads file context from filesystem
- Writes AI-generated code to filesystem
- Creates Git commits for AI changes with descriptive messages

## Migration Process

### Migration Script

**File:** `backend/migrate_to_filesystem.py`

**What it does:**
1. Reads all files from database
2. Writes content to filesystem (if not exists)
3. Initializes Git repository per project
4. Creates database backup (`lovable_dev.db.backup`)
5. Removes `content` column from `project_files` table
6. Creates indices

**Run migration:**
```bash
cd backend
python migrate_to_filesystem.py
```

**Output:**
```
Found 23 files to migrate...
--- Migrating Project 3 ---
  ✓ src/App.tsx already exists
  ✓ Git repository initialized
--- Creating database backup ---
✓ Backup created: lovable_dev.db.backup
--- Removing content column from database ---
✓ Content column removed successfully
=== Migration complete! ===
```

### Schema Updates

**File:** `backend/app/schemas/file.py`

**Changes:**
- `ProjectFileBase` - No content field
- `ProjectFileCreate` - Content optional (for API compatibility, not stored)
- `ProjectFile` - Content optional (populated from filesystem on read)

## API Behavior

### Get Project Files (`GET /api/v1/projects/{id}/files`)

**Before:**
```json
[
  {
    "id": 1,
    "filepath": "src/App.tsx",
    "content": "...stored in database..."
  }
]
```

**After:**
```json
[
  {
    "id": 1,
    "filepath": "src/App.tsx",
    "content": "...read from filesystem..."
  }
]
```

API response format **unchanged**, but source is now filesystem.

### Create/Update File

**Before:**
- Content saved to DB
- Filesystem sync

**After:**
- Content saved to filesystem
- Metadata saved to DB
- Git commit created

### AI Code Generation

**Before:**
- Files created/updated in DB
- Filesystem sync

**After:**
- Files created/updated in filesystem
- Metadata updated in DB
- Git commit with message: `"AI generated code: {user message}"`

## Benefits of New Architecture

### 1. Single Source of Truth
- Filesystem is the only place content is stored
- No sync issues between DB and files

### 2. Full Version History
- Every change is tracked in Git
- Can restore previous versions
- Can see who (user or AI) made changes and when

### 3. Standard Git Workflow
- Projects are standard Git repositories
- Can use any Git client/tools
- Can push to GitHub/GitLab if needed

### 4. Better Performance
- Database only stores lightweight metadata
- Faster queries
- No large TEXT fields in DB

### 5. Scalability
- File content doesn't bloat database
- Easy to backup (just filesystem)
- Easy to deploy (standard Git repos)

### 6. Developer Experience
- Can edit files directly on filesystem
- Can use standard dev tools
- Can commit manually if needed

## Testing

### Verify Database Migration

```bash
cd backend
python -c "
from app.db.database import SessionLocal
from app.models import ProjectFile

db = SessionLocal()
file = db.query(ProjectFile).first()
print(f'Has content attr: {hasattr(file, \"content\")}')
db.close()
"
```

**Expected output:** `Has content attr: False`

### Verify Filesystem Read

```bash
cd backend
python -c "
from app.services.project_service import ProjectService
from app.db.database import SessionLocal

db = SessionLocal()
files = ProjectService.get_project_files(db, 3, 1)
print(f'Files read: {len(files)}')
print(f'First file has content: {bool(files[0][\"content\"])}')
db.close()
"
```

**Expected output:**
```
Files read: 5
First file has content: True
```

### Verify Git Commits

```bash
cd backend/projects/project_3
git log --oneline
```

**Expected output:**
```
7e630cc Initial commit: Project scaffolding
```

## Rollback (If Needed)

If you need to rollback:

1. **Restore database backup:**
```bash
cd backend
cp lovable_dev.db.backup lovable_dev.db
```

2. **Revert code changes:**
```bash
git revert <commit-hash>
```

3. **Restart backend**

## Future Enhancements

### Planned Features

1. **Commit History API**
   - Endpoint to view commit history
   - Frontend UI to browse commits

2. **Time Travel**
   - Restore project to previous commit
   - Preview code at specific commit

3. **Branching**
   - Create experimental branches
   - Merge AI changes via PR workflow

4. **Git Push/Pull**
   - Sync with remote repositories
   - Push to GitHub from UI
   - Pull from external sources

5. **Diff Viewer**
   - Show changes before committing
   - Review AI changes before accepting

## Files Modified

### New Files
- `backend/app/services/git_service.py` - Git operations service
- `backend/migrate_to_filesystem.py` - Migration script
- `FILESYSTEM_AND_GIT_MIGRATION.md` - This documentation

### Modified Files
- `backend/app/models/file.py` - Removed `content` column
- `backend/app/services/project_service.py` - Read from filesystem
- `backend/app/services/chat_service.py` - Git commits on AI code
- `backend/app/services/filesystem_service.py` - Git init on project creation
- `backend/app/schemas/file.py` - Updated schemas

### Database Changes
- `project_files` table - Removed `content` column
- Backup created: `lovable_dev.db.backup`

## Summary

✅ **Migration Complete**

- File content removed from database
- Content now stored in filesystem only
- Git repositories initialized for all projects
- All services updated to use filesystem + Git
- API behavior unchanged from client perspective
- Full version control with commit history

The system now uses a **modern, Git-based architecture** that provides:
- Better performance
- Full version history
- Standard Git workflows
- Easy deployment
- Developer-friendly file access

**Next steps:** Test the updated system by creating/editing files through the API and verifying Git commits are created correctly.
