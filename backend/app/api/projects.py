from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithFiles,
    ProjectFile,
    ProjectFileCreate,
    ProjectFileUpdate,
)
from app.services import ProjectService
from app.services.filesystem_service import FileSystemService
from app.services.git_service import GitService

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
    file_update: ProjectFileUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Update a file's content"""
    content = file_update.content or ''
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


@router.get("/{project_id}/bundle")
def get_project_bundle(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all project files as a bundle for WebContainers
    Returns: { "files": { "path": "content", ... } }
    """
    # Verify ownership
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Get all files from filesystem
    files_list = FileSystemService.get_all_files(project_id)

    # Convert to WebContainers format: { "path": "content" }
    files_dict = {file["path"]: file["content"] for file in files_list}

    return {"files": files_dict}


# ===== GIT ENDPOINTS =====

@router.get("/{project_id}/git/history")
def get_git_history(
    project_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get Git commit history for a project

    Args:
        project_id: The project ID
        limit: Maximum number of commits to return (default: 20, max: 100)

    Returns:
        List of commits with hash, author, date, and message
    """
    # Verify ownership
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Limit to max 100 commits
    limit = min(limit, 100)

    commits = GitService.get_commit_history(project_id, limit)

    return {
        "project_id": project_id,
        "commits": commits,
        "total": len(commits)
    }


@router.get("/{project_id}/git/diff")
def get_git_diff(
    project_id: int,
    filepath: str = None,
    db: Session = Depends(get_db)
):
    """
    Get Git diff of uncommitted changes

    Args:
        project_id: The project ID
        filepath: Optional specific file to diff

    Returns:
        Git diff output
    """
    # Verify ownership
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    diff_output = GitService.get_diff(project_id, filepath)

    return {
        "project_id": project_id,
        "filepath": filepath,
        "diff": diff_output
    }


@router.get("/{project_id}/git/file/{commit_hash}")
def get_file_at_commit(
    project_id: int,
    commit_hash: str,
    filepath: str,
    db: Session = Depends(get_db)
):
    """
    Get file content at a specific commit

    Args:
        project_id: The project ID
        commit_hash: The Git commit hash
        filepath: The file path

    Returns:
        File content at the specified commit
    """
    # Verify ownership
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    content = GitService.get_file_at_commit(project_id, filepath, commit_hash)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filepath}' not found at commit {commit_hash}"
        )

    return {
        "project_id": project_id,
        "commit_hash": commit_hash,
        "filepath": filepath,
        "content": content
    }


@router.post("/{project_id}/git/restore/{commit_hash}")
def restore_to_commit(
    project_id: int,
    commit_hash: str,
    db: Session = Depends(get_db)
):
    """
    Restore project to a specific commit (creates a new commit)

    Args:
        project_id: The project ID
        commit_hash: The Git commit hash to restore to

    Returns:
        Success status
    """
    # Verify ownership
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    success = GitService.restore_commit(project_id, commit_hash)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore to commit"
        )

    return {
        "success": True,
        "message": f"Restored to commit {commit_hash[:7]}",
        "project_id": project_id,
        "commit_hash": commit_hash
    }
