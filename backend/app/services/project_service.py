from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Project, ProjectFile, ProjectStatus
from app.schemas import ProjectCreate, ProjectUpdate, ProjectFileCreate
from fastapi import HTTPException, status


class ProjectService:
    """Service for managing projects"""

    @staticmethod
    def create_project(db: Session, project: ProjectCreate, owner_id: int) -> Project:
        """Create a new project"""

        db_project = Project(
            **project.model_dump(),
            owner_id=owner_id,
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        # Create initial project structure
        ProjectService._create_initial_files(db, db_project.id, project.template)

        return db_project

    @staticmethod
    def get_project(db: Session, project_id: int, owner_id: int) -> Optional[Project]:
        """Get a project by ID"""

        project = db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == owner_id
        ).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return project

    @staticmethod
    def get_projects(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects for a user"""

        return db.query(Project).filter(
            Project.owner_id == owner_id
        ).offset(skip).limit(limit).all()

    @staticmethod
    def update_project(
        db: Session,
        project_id: int,
        owner_id: int,
        project_update: ProjectUpdate
    ) -> Project:
        """Update a project"""

        project = ProjectService.get_project(db, project_id, owner_id)

        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: int, owner_id: int) -> bool:
        """Delete a project"""

        project = ProjectService.get_project(db, project_id, owner_id)
        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def get_project_files(db: Session, project_id: int, owner_id: int) -> List[ProjectFile]:
        """Get all files for a project"""

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        return db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id
        ).all()

    @staticmethod
    def add_file_to_project(
        db: Session,
        project_id: int,
        owner_id: int,
        file_data: ProjectFileCreate
    ) -> ProjectFile:
        """Add a file to a project"""

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        db_file = ProjectFile(**file_data.model_dump())
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file

    @staticmethod
    def update_file(
        db: Session,
        file_id: int,
        project_id: int,
        owner_id: int,
        content: str
    ) -> ProjectFile:
        """Update a file's content"""

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        file = db.query(ProjectFile).filter(
            ProjectFile.id == file_id,
            ProjectFile.project_id == project_id
        ).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        file.content = content
        db.commit()
        db.refresh(file)
        return file

    @staticmethod
    def delete_file(db: Session, file_id: int, project_id: int, owner_id: int) -> bool:
        """Delete a file from a project"""

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        file = db.query(ProjectFile).filter(
            ProjectFile.id == file_id,
            ProjectFile.project_id == project_id
        ).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        db.delete(file)
        db.commit()
        return True

    @staticmethod
    def _create_initial_files(db: Session, project_id: int, template: str):
        """Create initial project structure based on template"""

        if template == "react-vite":
            initial_files = [
                {
                    "filename": "App.tsx",
                    "filepath": "src/App.tsx",
                    "language": "tsx",
                    "content": """import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white mb-4">
          Welcome to Your App
        </h1>
        <button
          onClick={() => setCount((count) => count + 1)}
          className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-all"
        >
          Count is {count}
        </button>
      </div>
    </div>
  )
}

export default App
""",
                },
                {
                    "filename": "main.tsx",
                    "filepath": "src/main.tsx",
                    "language": "tsx",
                    "content": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
                },
                {
                    "filename": "index.css",
                    "filepath": "src/index.css",
                    "language": "css",
                    "content": """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
}

body {
  margin: 0;
  padding: 0;
}
""",
                },
            ]

            for file_data in initial_files:
                file_data["project_id"] = project_id
                db_file = ProjectFile(**file_data)
                db.add(db_file)

            db.commit()
