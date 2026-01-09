from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import zipfile
import io
from pathlib import Path
import json
import httpx
from pydantic import BaseModel

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
from app.services.screenshot_service import ScreenshotService
from app.core.config import settings
from autogen_core.models import SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

router = APIRouter()

# Mock user ID for now (in production, get from JWT token)
MOCK_USER_ID = 1


class ProjectFromMessageRequest(BaseModel):
    message: str


class ProjectFromMessageResponse(BaseModel):
    project: Project
    initial_message: str


@router.post("/from-message", response_model=ProjectFromMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_project_from_message(
    request: ProjectFromMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new project from a user message.
    Uses AI to generate project name and description from the message.
    """
    user_message = request.message[:1000]  # Limit to 1000 characters

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Create AI prompt to generate project metadata
    system_prompt = """You are an AI assistant that helps create project metadata.
Given a user's message describing what they want to build, generate:
1. A concise project name (max 50 characters)
2. A clear project description (max 200 characters)

Return ONLY a JSON object with this exact structure:
{
  "name": "project name here",
  "description": "project description here"
}"""

    user_prompt = f"""Based on this user request, generate a project name and description:

User request: {user_message}

Remember to return ONLY the JSON object, nothing else."""

    # Call OpenAI to generate metadata
    http_client = httpx.AsyncClient()

    try:
        # Define model capabilities for non-OpenAI models (like DeepSeek)
        model_info = {
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "structured_output": True,
        }

        client = OpenAIChatCompletionClient(
            model=settings.OPENAI_MODEL,
            base_url=settings.OPENAI_API_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            model_capabilities=model_info,
            http_client=http_client,
        )

        messages = [
            SystemMessage(content=system_prompt),
            UserMessage(content=user_prompt, source="user"),
        ]

        result = await client.create(messages)
        response_content = result.content

        # Extract JSON from markdown code blocks if present (same as llm_edit_fixer.py)
        if response_content.strip().startswith("```"):
            response_content = response_content.split("```json")[-1].split("```")[0].strip()

        # Parse the JSON response
        metadata = json.loads(response_content)
        project_name = metadata.get("name", "New Project")[:50]
        project_description = metadata.get("description", user_message)[:200]

    except Exception as e:
        # Fallback if AI fails
        print(f"Error generating project metadata: {e}")
        project_name = "New Project"
        project_description = user_message[:200]
    finally:
        await http_client.aclose()

    # Create the project
    project_data = ProjectCreate(
        name=project_name,
        description=project_description
    )

    project = ProjectService.create_project(db, project_data, MOCK_USER_ID)

    return ProjectFromMessageResponse(
        project=project,
        initial_message=user_message
    )


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    return ProjectService.create_project(db, project, MOCK_USER_ID)


@router.get("", response_model=List[Project])
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
    """Get a specific project with its files (read from filesystem)"""
    project = ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Get files from filesystem (not database)
    files = FileSystemService.get_all_project_files(project_id)

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
        "thumbnail": project.thumbnail,
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
    """Get all files for a project (read from filesystem)"""
    # Verify project exists
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Get files from filesystem
    return FileSystemService.get_all_project_files(project_id)


@router.post("/{project_id}/files", response_model=ProjectFile, status_code=status.HTTP_201_CREATED)
def add_file_to_project(
    project_id: int,
    file_data: ProjectFileCreate,
    db: Session = Depends(get_db)
):
    """Add a file to a project (writes to filesystem only)"""
    # Verify project exists
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Write file to filesystem
    FileSystemService.write_file(project_id, file_data.filepath, file_data.content)

    # Get file timestamps from filesystem
    from datetime import datetime
    project_dir = FileSystemService.get_project_dir(project_id)
    file_path = project_dir / file_data.filepath
    stat = file_path.stat()
    created_at = datetime.fromtimestamp(stat.st_ctime)
    updated_at = datetime.fromtimestamp(stat.st_mtime)

    # Return file info (matching database schema for compatibility)
    return {
        "id": hash(file_data.filepath) % 100000,  # Generate pseudo-ID from filepath
        "project_id": project_id,
        "filename": Path(file_data.filepath).name,
        "filepath": file_data.filepath,
        "content": file_data.content,
        "language": file_data.language,
        "created_at": created_at,
        "updated_at": updated_at,
    }


@router.put("/{project_id}/files/{file_id}", response_model=ProjectFile)
def update_file(
    project_id: int,
    file_id: int,
    file_update: ProjectFileUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Update a file's content (writes to filesystem only)"""
    # Verify project exists
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Get the filepath - we need to find it by file_id
    # Since we're not using DB anymore, we need filepath from the update
    if not hasattr(file_update, 'filepath') or not file_update.filepath:
        raise HTTPException(status_code=400, detail="filepath is required for filesystem-based updates")

    content = file_update.content or ''
    FileSystemService.write_file(project_id, file_update.filepath, content)

    # Get file timestamps from filesystem
    from datetime import datetime
    project_dir = FileSystemService.get_project_dir(project_id)
    file_path = project_dir / file_update.filepath
    stat = file_path.stat()
    created_at = datetime.fromtimestamp(stat.st_ctime)
    updated_at = datetime.fromtimestamp(stat.st_mtime)

    return {
        "id": file_id,
        "project_id": project_id,
        "filename": Path(file_update.filepath).name,
        "filepath": file_update.filepath,
        "content": content,
        "language": getattr(file_update, 'language', 'text'),
        "created_at": created_at,
        "updated_at": updated_at,
    }


@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    project_id: int,
    file_id: int,
    filepath: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Delete a file from a project (deletes from filesystem only)"""
    # Verify project exists
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Delete from filesystem
    FileSystemService.delete_file(project_id, filepath)
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

    # Filter out internal agent state files before sending to WebContainer
    forbidden_files = ['.agent_state.json', 'agent_state.json']
    filtered_files = [
        file for file in files_list
        if not any(forbidden in file["path"] for forbidden in forbidden_files)
    ]

    # Convert to WebContainers format: { "path": "content" }
    files_dict = {file["path"]: file["content"] for file in filtered_files}

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


@router.get("/{project_id}/git/branch")
def get_current_branch(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get current Git branch for a project"""
    # Verify project exists
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    branch = GitService.get_current_branch(project_id)

    return {
        "project_id": project_id,
        "branch": branch
    }


@router.get("/{project_id}/git/config")
def get_git_config(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get Git remote configuration for a project"""
    # Verify project exists
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    config = GitService.get_remote_config(project_id)

    return {
        "project_id": project_id,
        **config
    }


@router.post("/{project_id}/git/config")
def set_git_config(
    project_id: int,
    config: dict,
    db: Session = Depends(get_db)
):
    """Set or update Git remote configuration for a project"""
    # Verify project exists
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    remote_url = config.get("remote_url", "")
    remote_name = config.get("remote_name", "origin")

    if not remote_url:
        raise HTTPException(status_code=400, detail="remote_url is required")

    success = GitService.set_remote_config(project_id, remote_url, remote_name)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to set remote configuration")

    return {
        "success": True,
        "message": f"Remote '{remote_name}' configured successfully",
        "project_id": project_id,
        "remote_name": remote_name,
        "remote_url": remote_url
    }


@router.post("/{project_id}/git/sync")
def sync_with_remote(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Sync project with remote repository (fetch, pull, commit, push)"""
    # Verify project exists
    ProjectService.get_project(db, project_id, MOCK_USER_ID)

    result = GitService.sync_with_remote(project_id)

    return {
        "project_id": project_id,
        **result
    }


@router.post("/{project_id}/thumbnail")
def update_project_thumbnail(
    project_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update project thumbnail by capturing screenshot of preview URL (DEPRECATED - use /thumbnail/upload)

    Args:
        project_id: The project ID
        data: JSON body with 'url' field containing the preview URL to capture

    Returns:
        Success status and project_id
    """
    # Verify project exists
    project = ProjectService.get_project(db, project_id, MOCK_USER_ID)

    preview_url = data.get("url", "")

    if not preview_url:
        raise HTTPException(status_code=400, detail="Preview URL is required")

    # Capture screenshot using Playwright
    thumbnail_data = ScreenshotService.capture_screenshot_sync(preview_url)

    if not thumbnail_data:
        raise HTTPException(
            status_code=500,
            detail="Failed to capture screenshot. Please ensure the preview URL is accessible."
        )

    # Update project thumbnail
    project.thumbnail = thumbnail_data
    db.commit()
    db.refresh(project)

    return {
        "success": True,
        "message": "Thumbnail updated successfully",
        "project_id": project_id
    }


@router.post("/{project_id}/thumbnail/upload")
def upload_project_thumbnail(
    project_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Upload project thumbnail from frontend (base64 screenshot)

    Args:
        project_id: The project ID
        data: JSON body with 'thumbnail' field containing base64 image data

    Returns:
        Success status and project_id
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"📸 Receiving thumbnail upload for project {project_id}")

    # Verify project exists
    project = ProjectService.get_project(db, project_id, MOCK_USER_ID)

    thumbnail_data = data.get("thumbnail", "")

    if not thumbnail_data:
        logger.error("❌ No thumbnail data provided")
        raise HTTPException(status_code=400, detail="Thumbnail data is required")

    # Validate base64 format
    if not thumbnail_data.startswith("data:image/"):
        logger.error("❌ Invalid thumbnail format (must be data URI)")
        raise HTTPException(status_code=400, detail="Thumbnail must be in data URI format")

    logger.info(f"✅ Thumbnail data received ({len(thumbnail_data)} bytes)")

    # Update project thumbnail
    project.thumbnail = thumbnail_data
    db.commit()
    db.refresh(project)

    logger.info(f"✅ Thumbnail saved to database for project {project_id}")

    return {
        "success": True,
        "message": "Thumbnail uploaded successfully",
        "project_id": project_id,
        "thumbnail_size": len(thumbnail_data)
    }


@router.post("/{project_id}/visual-edit")
def apply_visual_edit(
    project_id: int,
    edit_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Apply visual style changes directly to a component file.

    Args:
        project_id: The project ID
        edit_data: JSON body containing:
            - filepath: Path to the file to edit (e.g., 'src/App.tsx')
            - element_selector: Element tag name (e.g., 'button', 'div', 'Button')
            - style_changes: Dict of CSS properties (e.g., {'color': '#fff', 'backgroundColor': '#000'})

    Returns:
        Success status and updated file info
    """
    filepath = edit_data.get("filepath")
    element_selector = edit_data.get("element_selector")
    style_changes = edit_data.get("style_changes")

    if not filepath or not element_selector or not style_changes:
        raise HTTPException(
            status_code=400,
            detail="filepath, element_selector, and style_changes are required"
        )

    result = ProjectService.apply_visual_edits(
        db,
        project_id,
        MOCK_USER_ID,
        filepath,
        element_selector,
        style_changes
    )

    return result


@router.get("/{project_id}/download")
def download_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Download project as ZIP file

    Args:
        project_id: The project ID

    Returns:
        ZIP file containing all project files
    """
    # Verify project exists
    project = ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Get project directory path
    project_dir = Path(__file__).parent.parent.parent / "projects" / f"project_{project_id}"

    if not project_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="Project files not found on disk"
        )

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Walk through project directory and add all files
        for file_path in project_dir.rglob('*'):
            if file_path.is_file():
                # Skip .git directory and node_modules
                if '.git' in file_path.parts or 'node_modules' in file_path.parts:
                    continue

                # Add file to ZIP with relative path
                arcname = file_path.relative_to(project_dir)
                zip_file.write(file_path, arcname)

    # Reset buffer position to beginning
    zip_buffer.seek(0)

    # Create safe filename
    safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{safe_project_name or 'project'}.zip"

    # Return ZIP file as streaming response
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
