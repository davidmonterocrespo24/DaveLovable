# WebContainers Integration Guide

## Overview

This project now supports **physical file storage** to enable WebContainers integration. WebContainers allows running Node.js directly in the browser, providing a full development environment without backend servers.

## How It Works

### 1. File Storage

When AI generates code or you create a project:
- Files are saved to **SQLite database** (for querying/listing)
- Files are also written to **physical filesystem** at `backend/projects/project_{id}/`

### 2. Project Structure

Each project creates a complete Vite + React + TypeScript setup:

```
backend/projects/project_X/
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
├── tailwind.config.js     # Tailwind CSS config
├── postcss.config.js      # PostCSS config
├── index.html             # HTML entry point
└── src/
    ├── main.tsx           # React entry point
    ├── App.tsx            # Main App component
    ├── index.css          # Global styles with Tailwind
    └── components/        # Generated components go here
```

### 3. Bundle Endpoint

**GET** `/api/v1/projects/{project_id}/bundle`

Returns all project files in WebContainers format:

```json
{
  "files": {
    "package.json": "{\"name\":\"my-app\",...}",
    "index.html": "<!DOCTYPE html>...",
    "src/main.tsx": "import React from 'react'...",
    "src/components/Button.tsx": "export const Button = ()..."
  }
}
```

## Frontend Integration with WebContainers

### Step 1: Install WebContainers

```bash
cd front
npm install @webcontainer/api
```

### Step 2: Create WebContainer Service

Create `front/src/services/webcontainer.ts`:

```typescript
import { WebContainer } from '@webcontainer/api';

let webcontainerInstance: WebContainer | null = null;

export async function getWebContainer(): Promise<WebContainer> {
  if (!webcontainerInstance) {
    webcontainerInstance = await WebContainer.boot();
  }
  return webcontainerInstance;
}

export async function loadProject(projectId: number) {
  const container = await getWebContainer();

  // Fetch project files from backend
  const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/bundle`);
  const { files } = await response.json();

  // Mount files to WebContainer
  await container.mount(files);

  // Install dependencies
  const installProcess = await container.spawn('npm', ['install']);
  await installProcess.exit;

  // Start dev server
  const devProcess = await container.spawn('npm', ['run', 'dev']);

  // Listen for server URL
  devProcess.output.pipeTo(new WritableStream({
    write(data) {
      console.log(data);
    }
  }));

  // Wait for server to be ready
  container.on('server-ready', (port, url) => {
    console.log(`Server ready at ${url}`);
    // Update preview iframe src to this URL
  });
}
```

### Step 3: Update PreviewPanel

Update `front/src/components/editor/PreviewPanel.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { loadProject } from '@/services/webcontainer';

export const PreviewPanel = ({ projectId }: { projectId: number }) => {
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProject(projectId).then(() => {
      // WebContainer will emit 'server-ready' event with URL
      setLoading(false);
    });
  }, [projectId]);

  if (loading) {
    return <div>Loading preview...</div>;
  }

  return (
    <iframe
      src={previewUrl}
      className="w-full h-full border-0"
      allow="cross-origin-isolated"
    />
  );
};
```

### Step 4: Handle File Updates

When AI generates new code, reload the WebContainer:

```typescript
// In ChatPanel.tsx after receiving code changes
if (response.code_changes && response.code_changes.length > 0) {
  // Invalidate queries to refresh file list
  onCodeChange();

  // Reload WebContainer with updated files
  loadProject(projectId);
}
```

## API Reference

### File System Service

Backend service at `backend/app/services/filesystem_service.py`:

**Methods:**
- `create_project_structure(project_id, project_name)` - Creates complete project structure
- `write_file(project_id, filepath, content)` - Writes a file to disk
- `read_file(project_id, filepath)` - Reads a file from disk
- `delete_file(project_id, filepath)` - Deletes a file
- `delete_project(project_id)` - Deletes entire project directory
- `get_all_files(project_id)` - Returns all files as list of {path, content}

### Project Service Updates

All CRUD operations now sync with filesystem:
- **Create Project** → Creates physical directory structure
- **Add File** → Writes to DB and filesystem
- **Update File** → Updates DB and filesystem
- **Delete File** → Removes from DB and filesystem
- **Delete Project** → Removes from DB and filesystem

### Chat Service Updates

When AI generates code:
- Files are saved to database
- Files are written to filesystem at `src/components/{filename}`
- Bundle endpoint reflects changes immediately

## Benefits

1. **No Backend Compute** - Preview runs entirely in browser
2. **Real Node.js** - Full npm ecosystem available
3. **Instant Preview** - No build delays or server overhead
4. **Offline Capable** - Works without backend after initial load
5. **Scalable** - Each user runs their own container in-browser

## Security Notes

WebContainers require:
- HTTPS or localhost
- Cross-origin isolation headers:
  ```typescript
  // In vite.config.ts
  export default defineConfig({
    server: {
      headers: {
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin',
      }
    }
  })
  ```

## Testing

Test the bundle endpoint:

```bash
# Get project files bundle
curl http://localhost:8000/api/v1/projects/3/bundle | jq '.files | keys'

# Output:
[
  "index.html",
  "package.json",
  "postcss.config.js",
  "src/App.tsx",
  "src/index.css",
  "src/main.tsx",
  "tailwind.config.js",
  "tsconfig.json",
  "vite.config.ts"
]
```

## Next Steps

1. Install `@webcontainer/api` in frontend
2. Implement WebContainer service
3. Update PreviewPanel to use WebContainer
4. Add loading states and error handling
5. Handle hot module replacement (HMR)
6. Add console output display
7. Implement file watcher for auto-reload
