from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from app.models.project import ProjectStatus

if TYPE_CHECKING:
    from app.schemas.file import ProjectFile as ProjectFileType
else:
    ProjectFileType = 'ProjectFile'

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
    thumbnail: Optional[str] = None

    class Config:
        from_attributes = True

class Project(ProjectInDB):
    pass

class ProjectWithFiles(Project):
    files: List[ProjectFileType] = []
