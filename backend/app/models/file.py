from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class ProjectFile(Base):
    """
    ProjectFile model - stores only metadata.
    Actual file content is stored in the filesystem and versioned with Git.
    """

    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)  # Relative path from project root
    language = Column(String)  # tsx, ts, css, json, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="files")
