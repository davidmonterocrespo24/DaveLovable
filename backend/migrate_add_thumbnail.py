"""
Migration script to add thumbnail column to projects table
"""
import sqlite3
from pathlib import Path

def migrate():
    """Add thumbnail column to projects table"""
    # Path to database
    db_path = Path(__file__).parent / "lovable_dev.db"

    if not db_path.exists():
        print("ERROR: Database file not found. Please run init_db.py first.")
        return

    print("Starting migration...")
    print(f"Database: {db_path}")

    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'thumbnail' in columns:
            print("INFO: Column 'thumbnail' already exists. No migration needed.")
        else:
            # Add thumbnail column
            cursor.execute("""
                ALTER TABLE projects
                ADD COLUMN thumbnail TEXT
            """)
            conn.commit()
            print("SUCCESS: Added 'thumbnail' column to projects table")

        conn.close()
        print("\nMigration complete!")

    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    migrate()
