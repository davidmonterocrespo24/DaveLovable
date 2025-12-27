from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithFiles,
    ProjectFile,
    ProjectFileCreate,
)
from app.services import ProjectService

router = APIRouter()

# Mock user ID for now (in production, get from JWT token)
MOCK_USER_ID = 1


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    return ProjectService.create_project(db, project, MOCK_USER_ID)


@router.get("/", response_model=List[Project])
def get_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all projects for the current user"""
    return ProjectService.get_projects(db, MOCK_USER_ID, skip, limit)


@router.get("/{project_id}", response_model=ProjectWithFiles)
def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific project with its files"""
    project = ProjectService.get_project(db, project_id, MOCK_USER_ID)
    files = ProjectService.get_project_files(db, project_id, MOCK_USER_ID)

    # Convert to dict and add files
    project_dict = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "owner_id": project.owner_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "template": project.template,
        "framework": project.framework,
        "files": files,
    }

    return project_dict


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project"""
    return ProjectService.update_project(db, project_id, MOCK_USER_ID, project_update)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Delete a project"""
    ProjectService.delete_project(db, project_id, MOCK_USER_ID)
    return None


@router.get("/{project_id}/files", response_model=List[ProjectFile])
def get_project_files(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get all files for a project"""
    return ProjectService.get_project_files(db, project_id, MOCK_USER_ID)


@router.post("/{project_id}/files", response_model=ProjectFile, status_code=status.HTTP_201_CREATED)
def add_file_to_project(
    project_id: int,
    file_data: ProjectFileCreate,
    db: Session = Depends(get_db)
):
    """Add a file to a project"""
    return ProjectService.add_file_to_project(db, project_id, MOCK_USER_ID, file_data)


@router.put("/{project_id}/files/{file_id}", response_model=ProjectFile)
def update_file(
    project_id: int,
    file_id: int,
    content: str,
    db: Session = Depends(get_db)
):
    """Update a file's content"""
    return ProjectService.update_file(db, file_id, project_id, MOCK_USER_ID, content)


@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    """Delete a file from a project"""
    ProjectService.delete_file(db, file_id, project_id, MOCK_USER_ID)
    return None
