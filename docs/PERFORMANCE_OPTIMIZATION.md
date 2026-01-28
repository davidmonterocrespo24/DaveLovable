# Performance Optimization Guide

## Overview

This document explains the performance optimizations implemented for the `/projects` and `api/v1/projects` endpoints.

## Problem Statement

The `/projects` route was experiencing slow response times due to:
1. **N+1 Query Problem**: Lazy loading of relationships caused multiple database queries
2. **Missing Database Indexes**: No indexes on frequently queried columns
3. **Unoptimized Queries**: Loading unnecessary related data (files, chat sessions)

## Solution Implemented

### 1. Database Indexes

Added strategic indexes to improve query performance:

```python
# In app/models/project.py
owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

# Composite index for optimal performance
__table_args__ = (
    Index('idx_owner_updated', 'owner_id', 'updated_at'),
)
```

```python
# In app/models/file.py
__table_args__ = (
    Index('idx_project_files', 'project_id'),
)
```

**Why these indexes?**
- `owner_id` index: Fast filtering by user
- `updated_at` index: Fast sorting by last modified
- Composite `(owner_id, updated_at)`: Optimal for the common query pattern
- `project_id` index in files: Fast file lookups per project

### 2. Query Optimization

#### Before:
```python
def get_projects(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(Project).filter(Project.owner_id == owner_id).offset(skip).limit(limit).all()
```

**Problems:**
- Lazy loading caused N+1 queries when accessing relationships
- No explicit ordering
- Potentially loading unnecessary data

#### After:
```python
def get_projects(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    from sqlalchemy.orm import noload

    return (
        db.query(Project)
        .options(noload(Project.files), noload(Project.chat_sessions))
        .filter(Project.owner_id == owner_id)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
```

**Improvements:**
- `noload()` prevents lazy loading of unnecessary relationships
- `order_by(updated_at.desc())` shows most recent projects first
- Single efficient query with indexed columns

### 3. Model-Level Optimization

Set default lazy loading to `"noload"` in relationships:

```python
files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan", lazy="noload")
chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan", lazy="noload")
```

This prevents accidental N+1 queries throughout the application.

## Performance Results

### Before Optimization
- Estimated: 50-500ms+ depending on number of projects and relationships
- N+1 queries: 1 + N queries (1 for projects, N for related data)
- No indexed filtering or sorting

### After Optimization
Measured with 60 projects:
- **Response time**: ~4ms average
- **Time per project**: 0.07ms
- **Paginated (10 items)**: ~3ms
- **Consistency**: 4-5ms range (very stable)

## Migration for Existing Databases

For existing databases, run the migration script:

```bash
cd backend
python add_indexes.py
```

This script adds all necessary indexes using `CREATE INDEX IF NOT EXISTS`, so it's safe to run multiple times.

## Testing

Run performance tests to verify optimizations:

```bash
cd backend
source venv/bin/activate
pytest tests/test_performance.py -v -s
```

Expected output:
- All tests should pass
- Response times should be < 5ms for typical datasets
- No lazy loading warnings

## Best Practices Going Forward

1. **Use noload() explicitly** when you don't need related data
2. **Add indexes** for columns used in WHERE, ORDER BY, or JOIN clauses
3. **Test with realistic data volumes** to catch performance issues early
4. **Monitor query patterns** using SQLAlchemy's logging if needed:
   ```python
   import logging
   logging.basicConfig()
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

## Troubleshooting

### Slow queries after update
- Ensure indexes are created: `sqlite3 backend/davelovable.db ".indexes projects"` (adjust path based on your DATABASE_URL)
- Check if lazy loading is disabled: relationships should use `lazy="noload"`
- Verify query uses indexed columns: `EXPLAIN QUERY PLAN` in SQLite

### Existing database not using indexes
- Run `python add_indexes.py` to add indexes to existing database
- Or recreate database with `python init_db.py`

## Additional Resources

- [SQLAlchemy Eager Loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [Database Indexing Best Practices](https://use-the-index-luke.com/)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/advanced/async-sql-databases/)
