# WebContainers Integration

DaveLovable uses WebContainers by StackBlitz to run Node.js directly in the browser, enabling real-time previews without server-side execution.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Implementation Details](#implementation-details)
- [Browser Requirements](#browser-requirements)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What are WebContainers?

WebContainers is a technology by StackBlitz that allows running Node.js natively in the browser. This enables:

- **Real npm** - Install and use any npm package
- **Real Vite** - Hot Module Replacement (HMR) works
- **No Backend Compute** - Preview runs entirely in the browser
- **Instant Updates** - File changes reflect immediately
- **Offline Capable** - Works offline after initial load

### Benefits for DaveLovable

| Feature | Benefit |
|---------|---------|
| **Infinite Scalability** | Each user runs their own container |
| **No Server Costs** | Preview doesn't use backend resources |
| **Privacy** | Code runs locally in the browser |
| **Speed** | Near-instant preview updates |

---

## How It Works

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         BROWSER                              │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │   DaveLovable   │    │      WebContainer           │    │
│  │    Frontend     │───▶│  (Node.js in Browser)       │    │
│  │                 │    │                             │    │
│  │  - Code Editor  │    │  ┌─────────────────────┐   │    │
│  │  - Chat Panel   │    │  │   Vite Dev Server   │   │    │
│  │  - File Tree    │    │  │   (Port 5173)       │   │    │
│  │                 │    │  └─────────────────────┘   │    │
│  └─────────────────┘    │           │               │    │
│           │             │           ▼               │    │
│           │             │  ┌─────────────────────┐   │    │
│           │             │  │   Your React App    │   │    │
│           │             │  │   (Live Preview)    │   │    │
│           │             │  └─────────────────────┘   │    │
│           │             └─────────────────────────────┘    │
│           │                         │                      │
│           ▼                         ▼                      │
│  ┌─────────────────┐    ┌─────────────────────────┐       │
│  │  Preview Frame  │◀───│   Iframe Preview        │       │
│  │  (Device Modes) │    │   (localhost:xxxx)      │       │
│  └─────────────────┘    └─────────────────────────┘       │
│                                                            │
└────────────────────────────────────────────────────────────┘
                              │
                              │ Fetch Bundle
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│                                                              │
│  GET /api/v1/projects/{id}/bundle                           │
│                                                              │
│  Returns: { files: { "path": "content", ... } }             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Process Steps

1. **User opens project** → Frontend requests file bundle from backend
2. **Backend returns files** → All project files as path:content map
3. **Frontend initializes WebContainer** → Boots Node.js in browser
4. **Files mounted** → Project files written to WebContainer filesystem
5. **npm install runs** → Dependencies installed in browser
6. **Vite starts** → Development server starts with HMR
7. **Preview loads** → Running app displayed in iframe
8. **File changes** → Updates sync to WebContainer → HMR updates preview

---

## Architecture

### Frontend Components

#### WebContainer Service

**Location:** `front/src/services/webcontainer.ts`

```typescript
// Core functions
export async function bootWebContainer(): Promise<WebContainer>
export async function loadProject(projectId: string): Promise<string>
export function getWebContainer(): WebContainer | null

// File operations
export async function writeFile(path: string, content: string): Promise<void>
export async function readFile(path: string): Promise<string>

// Terminal operations
export async function runCommand(command: string): Promise<void>
```

#### Preview Component

**Location:** `front/src/components/editor/PreviewPanelWithWebContainer.tsx`

Features:
- WebContainer initialization
- Real-time console output display
- npm install progress
- Vite dev server status
- Device preview modes (mobile, tablet, desktop)
- Screenshot capture for thumbnails

### Backend API

#### Bundle Endpoint

**Endpoint:** `GET /api/v1/projects/{id}/bundle`

**Response:**
```json
{
  "files": {
    "package.json": "{ \"name\": \"project\"... }",
    "src/App.tsx": "import React from 'react'...",
    "src/main.tsx": "import { createRoot }...",
    "vite.config.ts": "import { defineConfig }..."
  }
}
```

---

## Implementation Details

### File Structure Conversion

The backend stores files in a flat structure. WebContainers require a tree structure:

```typescript
// Backend format (flat)
{
  "files": {
    "src/App.tsx": "...",
    "src/components/Button.tsx": "..."
  }
}

// WebContainer format (tree)
{
  "src": {
    "directory": {
      "App.tsx": {
        "file": {
          "contents": "..."
        }
      },
      "components": {
        "directory": {
          "Button.tsx": {
            "file": {
              "contents": "..."
            }
          }
        }
      }
    }
  }
}
```

The conversion is handled by `webcontainer.ts`:

```typescript
function flatToTree(files: Record<string, string>): FileSystemTree {
  const tree: FileSystemTree = {};
  
  for (const [path, content] of Object.entries(files)) {
    const parts = path.split('/');
    let current = tree;
    
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isFile = i === parts.length - 1;
      
      if (isFile) {
        current[part] = {
          file: { contents: content }
        };
      } else {
        current[part] = current[part] || { directory: {} };
        current = current[part].directory;
      }
    }
  }
  
  return tree;
}
```

### Boot Process

1. **Initialize WebContainer:**
   ```typescript
   const webcontainer = await WebContainer.boot();
   ```

2. **Mount Files:**
   ```typescript
   await webcontainer.mount(fileTree);
   ```

3. **Install Dependencies:**
   ```typescript
   const install = await webcontainer.spawn('npm', ['install']);
   await install.exit;
   ```

4. **Start Dev Server:**
   ```typescript
   const devProcess = await webcontainer.spawn('npm', ['run', 'dev']);
   ```

5. **Get Server URL:**
   ```typescript
   webcontainer.on('server-ready', (port, url) => {
     setPreviewUrl(url);
   });
   ```

### File Synchronization

When files are modified (via AI or editor):

```typescript
// Update single file
await webcontainer.fs.writeFile(filepath, content);

// HMR automatically updates the preview
```

---

## Browser Requirements

### Supported Browsers

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 89+ | ✅ Full |
| Edge | 89+ | ✅ Full |
| Brave | 1.22+ | ✅ Full |
| Firefox | - | ❌ Not supported |
| Safari | - | ❌ Not supported |

### Required Headers

WebContainers require Cross-Origin Isolation:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

These are configured in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp"
    }
  }
});
```

### Memory Requirements

- Minimum: 2GB available RAM
- Recommended: 4GB+ available RAM

---

## Configuration

### Vite Config

**Location:** `front/vite.config.ts`

```typescript
export default defineConfig({
  server: {
    port: 8080,
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp"
    }
  },
  optimizeDeps: {
    exclude: ['@webcontainer/api']
  }
});
```

### Project Template

Projects include a pre-configured Vite setup:

```
project_X/
├── package.json           # Vite + React dependencies
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript config
├── tailwind.config.js     # Tailwind CSS config
├── postcss.config.js      # PostCSS config
├── index.html             # Entry HTML
└── src/
    ├── main.tsx           # React entry
    ├── App.tsx            # Main component
    └── index.css          # Tailwind imports
```

### package.json Template

```json
{
  "name": "davelovable-project",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.2.0",
    "vite": "^5.0.0"
  }
}
```

---

## Console Output

The preview panel shows real-time console output:

### npm install
```
> npm install
⠙ Installing dependencies...
added 423 packages in 8s
```

### Vite dev server
```
> npm run dev

  VITE v5.0.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Error output
```
Error: Cannot find module 'react'
  at src/App.tsx:1:1
```

---

## Troubleshooting

### Common Issues

#### 1. WebContainer Not Loading

**Symptoms:** Preview stays blank or shows "Loading..."

**Solutions:**
- Check browser compatibility (Chrome/Edge 89+)
- Verify COOP/COEP headers in Network tab
- Check console for errors
- Try clearing browser cache

#### 2. npm Install Fails

**Symptoms:** Console shows npm errors

**Solutions:**
- Check package.json is valid JSON
- Verify all dependencies exist
- Check for network issues
- Try refreshing the page

#### 3. Preview Not Updating

**Symptoms:** Changes don't reflect in preview

**Solutions:**
- Check WebContainer is still running
- Verify file was saved successfully
- Try manual refresh
- Check Vite HMR connection

#### 4. Memory Issues

**Symptoms:** Browser becomes slow or crashes

**Solutions:**
- Close other tabs
- Increase available RAM
- Reduce project size
- Restart browser

### Debug Tools

#### Check WebContainer Status

```typescript
// In browser console
const wc = getWebContainer();
console.log('WebContainer:', wc);
console.log('Filesystem:', await wc.fs.readdir('/'));
```

#### Check Server Process

```typescript
// List running processes
const processes = await webcontainer.spawn('ps', []);
```

#### Manual Commands

```typescript
// Run any command in WebContainer
await webcontainer.spawn('npm', ['list']);
await webcontainer.spawn('cat', ['package.json']);
```

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `SharedArrayBuffer is not defined` | Missing COOP/COEP headers | Add required headers |
| `Failed to execute 'postMessage'` | Cross-origin issue | Check iframe origin |
| `ENOMEM` | Out of memory | Close tabs, increase RAM |
| `ENOENT` | File not found | Check file path |

---

## Performance Tips

### Optimize Boot Time

1. **Preload WebContainer:**
   ```typescript
   // Start boot early
   const bootPromise = WebContainer.boot();
   
   // Use when needed
   const webcontainer = await bootPromise;
   ```

2. **Cache installed packages:**
   WebContainers cache npm packages automatically.

3. **Minimize initial files:**
   Only include necessary files in initial bundle.

### Optimize Runtime

1. **Batch file updates:**
   ```typescript
   // Instead of multiple writes
   await Promise.all([
     wc.fs.writeFile('a.ts', contentA),
     wc.fs.writeFile('b.ts', contentB)
   ]);
   ```

2. **Use HMR effectively:**
   Vite HMR only updates changed modules.

3. **Monitor memory:**
   Close unused projects to free memory.

---

## Resources

- [WebContainers Documentation](https://webcontainers.io/guides/quickstart)
- [StackBlitz WebContainers API](https://webcontainers.io/api)
- [Vite Documentation](https://vitejs.dev/)
- [Cross-Origin Isolation](https://web.dev/cross-origin-isolation-guide/)
