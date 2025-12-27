"""
Migration script to remove content column from project_files table
and initialize Git repositories for existing projects.

This script:
1. Reads existing file content from database
2. Writes content to filesystem if not already there
3. Initializes Git repository for each project
4. Removes the content column from the database
"""

import sqlite3
from pathlib import Path
from app.services.filesystem_service import FileSystemService
from app.services.git_service import GitService

def migrate_to_filesystem():
    """Migrate from database storage to filesystem + Git"""

    # Connect to database
    db_path = Path("lovable_dev.db")
    if not db_path.exists():
        print("Database not found. Nothing to migrate.")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get all project files with content
    cursor.execute("""
        SELECT id, project_id, filename, filepath, content, language
        FROM project_files
    """)

    files = cursor.fetchall()

    if not files:
        print("No files found in database.")
    else:
        print(f"Found {len(files)} files to migrate...")

        # Group files by project
        projects = {}
        for file_id, project_id, filename, filepath, content, language in files:
            if project_id not in projects:
                projects[project_id] = []
            projects[project_id].append({
                'id': file_id,
                'filename': filename,
                'filepath': filepath,
                'content': content,
                'language': language
            })

        # Migrate each project
        for project_id, project_files in projects.items():
            print(f"\n--- Migrating Project {project_id} ---")
            project_dir = FileSystemService.get_project_dir(project_id)

            if not project_dir.exists():
                print(f"  Project directory doesn't exist. Skipping.")
                continue

            # Write files to filesystem
            for file_data in project_files:
                filepath = file_data['filepath']
                content = file_data['content']

                # Check if file already exists
                file_path = project_dir / filepath
                if file_path.exists():
                    print(f"  ✓ {filepath} already exists")
                else:
                    # Write file
                    FileSystemService.write_file(project_id, filepath, content)
                    print(f"  + {filepath} written to filesystem")

            # Initialize Git if not already initialized
            git_dir = project_dir / ".git"
            if git_dir.exists():
                print(f"  ✓ Git repository already initialized")
            else:
                success = GitService.init_repository(project_id)
                if success:
                    print(f"  ✓ Git repository initialized")
                else:
                    print(f"  ✗ Failed to initialize Git repository")

    # Create backup of database
    print("\n--- Creating database backup ---")
    backup_path = db_path.with_suffix('.db.backup')
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")

    # Check if content column exists
    cursor.execute("PRAGMA table_info(project_files)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'content' in column_names:
        print("\n--- Removing content column from database ---")

        # SQLite doesn't support DROP COLUMN directly, need to recreate table
        # 1. Create new table without content column
        cursor.execute("""
            CREATE TABLE project_files_new (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                filename VARCHAR NOT NULL,
                filepath VARCHAR NOT NULL,
                language VARCHAR,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)

        # 2. Copy data from old table to new table
        cursor.execute("""
            INSERT INTO project_files_new (id, project_id, filename, filepath, language, created_at, updated_at)
            SELECT id, project_id, filename, filepath, language, created_at, updated_at
            FROM project_files
        """)

        # 3. Drop old table
        cursor.execute("DROP TABLE project_files")

        # 4. Rename new table
        cursor.execute("ALTER TABLE project_files_new RENAME TO project_files")

        # 5. Recreate indices
        cursor.execute("CREATE INDEX ix_project_files_id ON project_files (id)")

        conn.commit()
        print("✓ Content column removed successfully")
    else:
        print("\n✓ Content column already removed")

    conn.close()
    print("\n=== Migration complete! ===")
    print(f"Backup available at: {backup_path}")
    print("\nAll file content is now stored in:")
    print(f"  - Filesystem: backend/projects/project_*/")
    print(f"  - Version control: Git repositories in each project")

if __name__ == "__main__":
    migrate_to_filesystem()
