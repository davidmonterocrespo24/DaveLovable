from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProjectFileBase(BaseModel):
    filename: str
    filepath: str
    content: str
    language: Optional[str] = None

class ProjectFileCreate(ProjectFileBase):
    project_id: int

class ProjectFileUpdate(BaseModel):
    filename: Optional[str] = None
    filepath: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None

class ProjectFileInDB(ProjectFileBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectFile(ProjectFileInDB):
    pass
