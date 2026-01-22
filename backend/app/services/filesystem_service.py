import json
import os
import shutil
import stat
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings


class FileSystemService:
    """Service for managing physical project files on disk"""

    @staticmethod
    def _handle_remove_readonly(func, path, exc_info):
        """
        Error handler for Windows readonly file deletion.
        Used with shutil.rmtree to handle permission errors.
        """
        # Check if it's a permission error
        if not os.access(path, os.W_OK):
            # Change the file to be writable and try again
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            func(path)
        else:
            raise

    @staticmethod
    def get_project_dir(project_id: int) -> Path:
        """Get the directory path for a project"""
        base_dir = Path(settings.PROJECTS_BASE_DIR)
        project_dir = base_dir / f"project_{project_id}"
        return project_dir

    @staticmethod
    def create_project_structure(project_id: int, project_name: str) -> Dict[str, str]:
        """
        Create physical project structure with initial files and initialize Git
        Returns a dict of created files and their content
        """
        from app.services.git_service import GitService

        project_dir = FileSystemService.get_project_dir(project_id)

        # Create project directory if it doesn't exist
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create basic project structure
        src_dir = project_dir / "src"
        src_dir.mkdir(exist_ok=True)

        components_dir = src_dir / "components"
        components_dir.mkdir(exist_ok=True)

        # Create package.json
        package_json = {
            "name": project_name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "type": "module",
            "scripts": {"dev": "vite", "build": "tsc && vite build", "preview": "vite preview"},
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "lucide-react": "^0.263.1",
                "date-fns": "^2.30.0",
                "clsx": "^2.1.0",
                "react-router-dom": "^6.26.0",
                "axios": "^1.7.0",
                "zustand": "^4.5.0",
                "@tanstack/react-query": "^5.0.0",
                "framer-motion": "^11.0.0",
                "react-hook-form": "^7.51.0",
                "zod": "^3.22.0",
                "firebase": "^10.8.0",
            },
            "devDependencies": {
                "@types/react": "^18.3.12",
                "@types/react-dom": "^18.3.1",
                "@vitejs/plugin-react": "^4.3.4",
                "typescript": "^5.8.0",
                "vite": "^5.4.11",
                "tailwindcss": "^3.4.17",
                "autoprefixer": "^10.4.20",
                "postcss": "^8.4.49",
            },
        }

        # Create vite.config.ts
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  }
})
"""

        # Create tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True,
            },
            "include": ["src"],
            "references": [{"path": "./tsconfig.node.json"}],
        }

        # Create tsconfig.node.json
        tsconfig_node = {
            "compilerOptions": {
                "composite": True,
                "skipLibCheck": True,
                "module": "ESNext",
                "moduleResolution": "bundler",
                "allowSyntheticDefaultImports": True,
            },
            "include": ["vite.config.ts"],
        }

        # Create tailwind.config.js
        tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""

        # Create postcss.config.js
        postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""

        # Read console logger script template
        console_logger_path = Path(__file__).parent.parent / "templates" / "console_logger.js"
        try:
            with open(console_logger_path, encoding="utf-8") as f:
                console_logger_script = f.read()
        except FileNotFoundError:
            console_logger_script = "// Console logger not found"

        # Create index.html with injected console logger
        index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <!-- Browser Console Logger for AI Agent -->
    <script>
{console_logger_script}
    </script>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

        # Create src/main.tsx
        main_tsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""

        # Create src/App.tsx
        app_tsx = (
            """import React from 'react'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to """
            + project_name
            + """
        </h1>
        <p className="text-lg text-gray-600">
          Start building your amazing application!
        </p>
      </div>
    </div>
  )
}

export default App
"""
        )

        # Create src/index.css
        index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
"""

        # Write all files
        files_created = {}

        (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))
        files_created["package.json"] = json.dumps(package_json, indent=2)

        (project_dir / "vite.config.ts").write_text(vite_config)
        files_created["vite.config.ts"] = vite_config

        (project_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
        files_created["tsconfig.json"] = json.dumps(tsconfig, indent=2)

        (project_dir / "tsconfig.node.json").write_text(json.dumps(tsconfig_node, indent=2))
        files_created["tsconfig.node.json"] = json.dumps(tsconfig_node, indent=2)

        (project_dir / "tailwind.config.js").write_text(tailwind_config)
        files_created["tailwind.config.js"] = tailwind_config

        (project_dir / "postcss.config.js").write_text(postcss_config)
        files_created["postcss.config.js"] = postcss_config

        (project_dir / "index.html").write_text(index_html)
        files_created["index.html"] = index_html

        (src_dir / "main.tsx").write_text(main_tsx)
        files_created["src/main.tsx"] = main_tsx

        (src_dir / "App.tsx").write_text(app_tsx)
        files_created["src/App.tsx"] = app_tsx

        (src_dir / "index.css").write_text(index_css)
        files_created["src/index.css"] = index_css

        # Initialize Git repository
        GitService.init_repository(project_id)

        return files_created

    # Firebase Template Files
    FIREBASE_TEMPLATE_FILES = {
        ".env.local": """# Firebase Proxy Configuration
# IMPORTANT: Never commit this file to Git! It's already in .gitignore

# API URL - Backend proxy endpoint
VITE_API_URL=http://localhost:8000

# Project Identifier - DO NOT CHANGE THIS VALUE
# This ensures your Firestore collections are unique across all projects
VITE_PROJECT_ID={project_id}
""",
        "src/lib/firestore.ts": """{firestore_client_content}""",
        "README.firebase.md": """# Firebase Proxy Setup

## Overview

This project uses a **secure proxy architecture** for Firebase Firestore. All database operations go through your backend, keeping Firebase credentials safe.

### ✅ Benefits
- **Secure**: Firebase credentials never leave the backend
- **Simple**: No Firebase setup needed in your project
- **Multi-project**: Automatic collection prefixing isolates data

## How It Works

1. Your frontend calls functions like `addDoc()`, `getDocs()`, etc.
2. These functions send HTTP requests to your backend proxy
3. The backend handles Firebase operations with real credentials
4. Your data is automatically prefixed with `proj_{project_id}_`

## Usage

### Import from `@/lib/firestore`

```typescript
import { db, collection, addDoc, getDocs, doc, getDoc, updateDoc, deleteDoc } from '@/lib/firestore';

// ✅ Add a document
const docRef = await addDoc(collection(db, 'users'), {
  name: 'John Doe',
  email: 'john@example.com',
  createdAt: serverTimestamp()
});
console.log('Created document:', docRef.id);

// ✅ Get all documents
const snapshot = await getDocs(collection(db, 'users'));
const users = snapshot.docs.map(doc => ({
  id: doc.id,
  ...doc.data()
}));

// ✅ Get single document
const userRef = doc(db, 'users', 'user123');
const userDoc = await getDoc(userRef);
if (userDoc.exists) {
  console.log('User data:', userDoc.data());
}

// ✅ Update document
await updateDoc(userRef, {
  name: 'Jane Smith',
  updatedAt: serverTimestamp()
});

// ✅ Delete document
await deleteDoc(userRef);
```

### API Reference

All standard Firestore operations are supported:

- `collection(db, path)` - Get collection reference
- `doc(db, path, id)` - Get document reference
- `addDoc(collectionRef, data)` - Add new document
- `setDoc(docRef, data)` - Set document with ID
- `getDoc(docRef)` - Get single document
- `getDocs(collectionRef)` - Get all documents
- `updateDoc(docRef, data)` - Update document
- `deleteDoc(docRef)` - Delete document
- `serverTimestamp()` - Server timestamp

### Environment Variables

Your `.env.local` file contains:

```env
# Backend API URL
VITE_API_URL=http://localhost:8000

# Your unique project ID (DO NOT CHANGE)
VITE_PROJECT_ID={project_id}
```

**IMPORTANT**: Make sure your backend is running on `http://localhost:8000`

## Collection Prefixing

Your collections are automatically prefixed in Firestore:
- Your code: `collection(db, 'users')`
- Actual collection: `proj_{project_id}_users`

This allows multiple projects to share one Firebase database safely.

## Security

**✅ Credentials are secure**: Firebase service account credentials stay in the backend

**✅ No configuration needed**: The backend handles all Firebase setup

**✅ No Firebase SDK**: Your frontend doesn't need Firebase packages installed

## For Production

When deploying:

1. Update `VITE_API_URL` in `.env.local` to your production backend URL
2. Ensure your backend has the Firebase service account credentials
3. The proxy endpoints are at `/api/v1/firebase/projects/{project_id}/firestore/*`

## Troubleshooting

**"Failed to add/get document" errors**:
- Make sure backend is running on port 8000
- Check VITE_API_URL in `.env.local`
- Check browser console for CORS errors

**"Firebase not activated" error**:
- This means Firebase wasn't enabled for your project
- Ask the AI agent to activate Firebase

## Resources

- Backend proxy code: `backend/app/api/firebase_proxy.py`
- Frontend client: `src/lib/firestore.ts`
- Firestore proxy architecture documentation
""",
        ".firebase-state.json": """{"activated": true, "features": [], "activated_at": ""}"""
    }

    @staticmethod
    def activate_firebase(project_id: int, features: List[str]) -> Dict:
        """
        Activate Firebase in an existing project

        Args:
            project_id: Project ID
            features: List of Firebase features to activate ["firestore", "auth", "storage"]

        Returns:
            Dict with created files and status
        """
        import hashlib
        import time

        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists():
            raise ValueError(f"Project {project_id} does not exist")

        # Generate unique project identifier for Firestore collection prefixing
        # Format: {project_id}_{timestamp_hash} (e.g., "1_a3f2b9")
        # This ensures collections are unique even if project IDs are reused
        timestamp = str(int(time.time()))
        hash_input = f"{project_id}_{timestamp}".encode()
        unique_hash = hashlib.sha256(hash_input).hexdigest()[:6]
        project_unique_id = f"{project_id}_{unique_hash}"

        created_files = []

        # Load firestore proxy client template
        firestore_client_path = Path(__file__).parent.parent / "templates" / "firebase" / "firestore_proxy_client.ts"
        try:
            with open(firestore_client_path, encoding="utf-8") as f:
                firestore_client_content = f.read()
        except FileNotFoundError:
            firestore_client_content = "// Firestore proxy client template not found"

        # Create Firebase template files with project_unique_id and project_id injected
        for filepath, content_template in FileSystemService.FIREBASE_TEMPLATE_FILES.items():
            # Replace placeholder with actual unique ID
            content = content_template.replace("{project_unique_id}", project_unique_id)
            # Replace project_id placeholder (for API calls)
            content = content.replace("{project_id}", str(project_id))
            # Replace firestore client placeholder
            content = content.replace("{firestore_client_content}", firestore_client_content)
            FileSystemService.write_file(project_id, filepath, content)
            created_files.append(filepath)

        # Update .firebase-state.json with activation details
        from datetime import datetime
        firebase_state = {
            "activated": True,
            "features": features,
            "activated_at": datetime.utcnow().isoformat(),
            "project_unique_id": project_unique_id,
            "collection_prefix": f"proj_{project_unique_id}_"
        }
        FileSystemService.write_file(project_id, ".firebase-state.json", json.dumps(firebase_state, indent=2))

        # Update package.json to add Firebase dependencies
        package_json_path = project_dir / "package.json"
        if package_json_path.exists():
            package_data = json.loads(package_json_path.read_text(encoding="utf-8"))

            # Add Firebase SDK to dependencies
            if "dependencies" not in package_data:
                package_data["dependencies"] = {}

            package_data["dependencies"]["firebase"] = "^10.8.0"

            # Write updated package.json
            package_json_path.write_text(json.dumps(package_data, indent=2), encoding="utf-8")
            created_files.append("package.json (updated)")

        # Update .gitignore to include .env.local if not already there
        gitignore_path = project_dir / ".gitignore"
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text(encoding="utf-8")
            if ".env.local" not in gitignore_content:
                gitignore_content += "\n# Firebase environment variables\n.env.local\n"
                gitignore_path.write_text(gitignore_content, encoding="utf-8")
        else:
            gitignore_content = "# Firebase environment variables\n.env.local\n"
            gitignore_path.write_text(gitignore_content, encoding="utf-8")
            created_files.append(".gitignore")

        return {
            "success": True,
            "created_files": created_files,
            "features": features,
            "project_unique_id": project_unique_id,
            "collection_prefix": f"proj_{project_unique_id}_",
            "message": f"Firebase activated with features: {', '.join(features)}. Collection prefix: proj_{project_unique_id}_"
        }

    @staticmethod
    def write_file(project_id: int, filepath: str, content: str) -> None:
        """Write a file to the project directory"""
        project_dir = FileSystemService.get_project_dir(project_id)
        file_path = project_dir / filepath

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path.write_text(content, encoding="utf-8")

    @staticmethod
    def read_file(project_id: int, filepath: str) -> Optional[str]:
        """Read a file from the project directory"""
        project_dir = FileSystemService.get_project_dir(project_id)
        file_path = project_dir / filepath

        if not file_path.exists():
            return None

        return file_path.read_text(encoding="utf-8")

    @staticmethod
    def delete_file(project_id: int, filepath: str) -> bool:
        """Delete a file from the project directory"""
        project_dir = FileSystemService.get_project_dir(project_id)
        file_path = project_dir / filepath

        if not file_path.exists():
            return False

        file_path.unlink()
        return True

    @staticmethod
    def delete_project(project_id: int) -> bool:
        """Delete entire project directory"""
        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists():
            return False

        # Use onerror callback to handle readonly files on Windows
        shutil.rmtree(project_dir, onerror=FileSystemService._handle_remove_readonly)
        return True

    @staticmethod
    def get_all_files(project_id: int) -> List[Dict[str, str]]:
        """Get all files in a project as a list of {path, content} dicts"""
        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists():
            return []

        # Directories to exclude from bundle (node_modules, .git, build artifacts, etc.)
        excluded_dirs = {
            "node_modules",
            ".git",
            "dist",
            "build",
            ".vite",
            "coverage",
            ".turbo",
            ".next",
            ".cache",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
        }

        # File patterns to exclude
        excluded_files = {
            ".DS_Store",
            "Thumbs.db",
            ".env",
            ".env.local",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
        }

        files = []
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(project_dir)

                # Check if file is in an excluded directory
                if any(excluded_dir in relative_path.parts for excluded_dir in excluded_dirs):
                    continue

                # Check if file name is excluded
                if file_path.name in excluded_files:
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8")
                    files.append({"path": str(relative_path).replace("\\", "/"), "content": content})
                except Exception:
                    # Skip binary files or files that can't be read
                    pass

        return files

    @staticmethod
    def get_all_project_files(project_id: int) -> List[Dict]:
        """
        Get all files in a project with metadata (for API responses).
        Returns list of file objects compatible with frontend expectations.
        """
        project_dir = FileSystemService.get_project_dir(project_id)

        if not project_dir.exists():
            return []

        # Directories to exclude
        excluded_dirs = {
            "node_modules",
            ".git",
            "dist",
            "build",
            ".vite",
            "coverage",
            ".turbo",
            ".next",
            ".cache",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
        }

        # Files to exclude
        excluded_files = {
            ".DS_Store",
            "Thumbs.db",
            ".env",
            ".env.local",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            ".gitignore",
            ".browser_logs.json",
            ".agent_state.json",
        }

        # Language mapping by extension
        language_map = {
            ".tsx": "tsx",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".js": "javascript",
            ".css": "css",
            ".html": "html",
            ".json": "json",
            ".md": "markdown",
            ".py": "python",
            ".yml": "yaml",
            ".yaml": "yaml",
        }

        files = []
        file_id = 1  # Generate sequential IDs for frontend

        for file_path in sorted(project_dir.rglob("*")):
            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(project_dir)

            # Check if file is in an excluded directory
            if any(excluded_dir in relative_path.parts for excluded_dir in excluded_dirs):
                continue

            # Check if file name is excluded
            if file_path.name in excluded_files:
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                filepath_str = str(relative_path).replace("\\", "/")
                extension = file_path.suffix
                language = language_map.get(extension, "text")

                # Get file timestamps from filesystem
                from datetime import datetime

                stat = file_path.stat()
                created_at = datetime.fromtimestamp(stat.st_ctime)
                updated_at = datetime.fromtimestamp(stat.st_mtime)

                files.append(
                    {
                        "id": file_id,
                        "project_id": project_id,
                        "filename": file_path.name,
                        "filepath": filepath_str,
                        "content": content,
                        "language": language,
                        "created_at": created_at,
                        "updated_at": updated_at,
                    }
                )
                file_id += 1
            except Exception:
                # Skip binary files or files that can't be read
                pass

        return files
