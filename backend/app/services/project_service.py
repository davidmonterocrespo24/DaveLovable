from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Project, ProjectFile, ProjectStatus
from app.schemas import ProjectCreate, ProjectUpdate, ProjectFileCreate
from app.services.filesystem_service import FileSystemService
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

        # Create initial project structure (both DB and filesystem)
        ProjectService._create_initial_files(db, db_project.id, db_project.name, project.template)

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

        # Delete physical files
        FileSystemService.delete_project(project_id)

        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def get_project_files(db: Session, project_id: int, owner_id: int) -> List[dict]:
        """Get all files for a project from filesystem"""

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        # Get file metadata from database
        db_files = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id
        ).all()

        # Read content from filesystem
        files_with_content = []
        for db_file in db_files:
            content = FileSystemService.read_file(project_id, db_file.filepath)
            files_with_content.append({
                "id": db_file.id,
                "project_id": db_file.project_id,
                "filename": db_file.filename,
                "filepath": db_file.filepath,
                "content": content or "",
                "language": db_file.language,
                "created_at": db_file.created_at,
                "updated_at": db_file.updated_at,
            })

        return files_with_content

    @staticmethod
    def add_file_to_project(
        db: Session,
        project_id: int,
        owner_id: int,
        file_data: ProjectFileCreate
    ) -> dict:
        """Add a file to a project"""
        from app.services.git_service import GitService

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        # Extract content from file_data
        content = file_data.content if hasattr(file_data, 'content') else ""

        # Create file metadata in database (without content)
        file_dict = file_data.model_dump()
        file_dict.pop('content', None)  # Remove content if present

        db_file = ProjectFile(**file_dict)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # Write to filesystem
        FileSystemService.write_file(project_id, db_file.filepath, content)

        # Commit to Git
        GitService.commit_changes(
            project_id,
            f"Add file: {db_file.filepath}",
            [db_file.filepath]
        )

        return {
            "id": db_file.id,
            "project_id": db_file.project_id,
            "filename": db_file.filename,
            "filepath": db_file.filepath,
            "content": content,
            "language": db_file.language,
            "created_at": db_file.created_at,
            "updated_at": db_file.updated_at,
        }

    @staticmethod
    def update_file(
        db: Session,
        file_id: int,
        project_id: int,
        owner_id: int,
        content: str
    ) -> dict:
        """Update a file's content"""
        from app.services.git_service import GitService

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

        # Update filesystem
        FileSystemService.write_file(project_id, file.filepath, content)

        # Commit to Git
        GitService.commit_changes(
            project_id,
            f"Update file: {file.filepath}",
            [file.filepath]
        )

        # Update timestamp in database
        from datetime import datetime
        file.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(file)

        return {
            "id": file.id,
            "project_id": file.project_id,
            "filename": file.filename,
            "filepath": file.filepath,
            "content": content,
            "language": file.language,
            "created_at": file.created_at,
            "updated_at": file.updated_at,
        }

    @staticmethod
    def delete_file(db: Session, file_id: int, project_id: int, owner_id: int) -> bool:
        """Delete a file from a project"""
        from app.services.git_service import GitService

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

        filepath = file.filepath

        # Delete from filesystem
        FileSystemService.delete_file(project_id, filepath)

        # Delete from database
        db.delete(file)
        db.commit()

        # Commit deletion to Git
        GitService.commit_changes(
            project_id,
            f"Delete file: {filepath}"
        )

        return True

    @staticmethod
    def _create_initial_files(db: Session, project_id: int, project_name: str, template: str):
        """Create initial project structure based on template"""

        # Create physical project structure (includes Git init)
        FileSystemService.create_project_structure(project_id, project_name)

        if template == "react-vite":
            # Only store metadata in database (content is in filesystem)
            initial_files = [
                {
                    "project_id": project_id,
                    "filename": "App.tsx",
                    "filepath": "src/App.tsx",
                    "language": "tsx",
                },
                {
                    "project_id": project_id,
                    "filename": "main.tsx",
                    "filepath": "src/main.tsx",
                    "language": "tsx",
                },
                {
                    "project_id": project_id,
                    "filename": "index.css",
                    "filepath": "src/index.css",
                    "language": "css",
                },
                {
                    "project_id": project_id,
                    "filename": "tsconfig.node.json",
                    "filepath": "tsconfig.node.json",
                    "language": "json",
                },
            ]

            for file_data in initial_files:
                db_file = ProjectFile(**file_data)
                db.add(db_file)

            db.commit()
