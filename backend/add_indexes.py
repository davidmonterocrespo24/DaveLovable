#!/usr/bin/env python3
"""
Migration script to add performance indexes to the database.
Run this script to add indexes to existing databases.
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db.database import engine


def add_indexes():
    """Add performance indexes to the database"""
    print("Adding performance indexes to database...")
    
    with engine.begin() as conn:
        # Add index on owner_id if it doesn't exist
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_projects_owner_id ON projects(owner_id)"
            ))
            print("✓ Created index on projects.owner_id")
        except Exception as e:
            print(f"  Index on projects.owner_id might already exist: {e}")
        
        # Add index on updated_at if it doesn't exist
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_projects_updated_at ON projects(updated_at)"
            ))
            print("✓ Created index on projects.updated_at")
        except Exception as e:
            print(f"  Index on projects.updated_at might already exist: {e}")
        
        # Add composite index on (owner_id, updated_at) for optimal query performance
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_owner_updated ON projects(owner_id, updated_at)"
            ))
            print("✓ Created composite index on projects(owner_id, updated_at)")
        except Exception as e:
            print(f"  Composite index might already exist: {e}")
        
        # Add index on project_files.project_id if it doesn't exist
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_project_files ON project_files(project_id)"
            ))
            print("✓ Created index on project_files.project_id")
        except Exception as e:
            print(f"  Index on project_files.project_id might already exist: {e}")
    
    print("\n✅ Database indexes added successfully!")
    print("\nIndexes created:")
    print("  - projects.owner_id (ix_projects_owner_id)")
    print("  - projects.updated_at (ix_projects_updated_at)")
    print("  - projects(owner_id, updated_at) - composite (idx_owner_updated)")
    print("  - project_files.project_id (idx_project_files)")


if __name__ == "__main__":
    add_indexes()
