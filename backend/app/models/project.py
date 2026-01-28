import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.database import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Project configuration
    template = Column(String, default="react-vite")
    framework = Column(String, default="react")
    thumbnail = Column(Text, nullable=True)  # Base64 encoded screenshot

    # Relationships
    owner = relationship("User", back_populates="projects")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan", lazy="noload")
    chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan", lazy="noload")

    # Add composite index for common queries (owner_id, updated_at DESC)
    __table_args__ = (
        Index('idx_owner_updated', 'owner_id', 'updated_at'),
    )
