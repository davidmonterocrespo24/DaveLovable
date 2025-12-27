from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.project import ProjectStatus

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    template: str = "react-vite"
    framework: str = "react"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    template: Optional[str] = None
    framework: Optional[str] = None

class ProjectInDB(ProjectBase):
    id: int
    status: ProjectStatus
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Project(ProjectInDB):
    pass

class ProjectWithFiles(Project):
    from app.schemas.file import ProjectFile
    files: List[ProjectFile] = []
