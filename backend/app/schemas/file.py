from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectFileBase(BaseModel):
    """Base schema for file metadata (no content - that's in filesystem)"""

    filename: str
    filepath: str
    language: Optional[str] = None


class ProjectFileCreate(ProjectFileBase):
    """Schema for creating a file (content passed separately)"""

    project_id: int
    content: Optional[str] = None  # Optional, for API compatibility, not stored in DB


class ProjectFileUpdate(BaseModel):
    """Schema for updating file metadata"""

    filename: Optional[str] = None
    filepath: Optional[str] = None
    content: Optional[str] = None  # For API compatibility, not stored in DB
    language: Optional[str] = None


class ProjectFileInDB(ProjectFileBase):
    """File metadata stored in database (no content)"""

    id: int
    project_id: int
    created_at: Optional[datetime] = None  # Optional for filesystem-only mode
    updated_at: Optional[datetime] = None  # Optional for filesystem-only mode

    class Config:
        from_attributes = True


class ProjectFile(ProjectFileInDB):
    """File response schema (content added from filesystem when needed)"""

    content: Optional[str] = None  # Populated from filesystem, not from DB
