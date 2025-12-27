# Backend API Tests

Automated tests for the FastAPI backend.

## Setup

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install test dependencies
pip install pytest pytest-asyncio httpx
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run specific test class
pytest tests/test_api.py::TestProjectAPI

# Run specific test
pytest tests/test_api.py::TestProjectAPI::test_create_project
```

## Test Coverage

### Project API Tests
- `test_create_project` - Creating new projects
- `test_list_projects` - Listing all projects
- `test_get_project` - Getting a specific project
- `test_update_project` - Updating project details
- `test_delete_project` - Deleting projects

### File API Tests
- `test_create_file` - Creating files in a project
- `test_list_files` - Listing files in a project
- `test_update_file` - Updating file content
- `test_delete_file` - Deleting files

### Chat API Tests
- `test_send_message` - Sending messages to AI (requires OPENAI_API_KEY)
- `test_list_sessions` - Listing chat sessions

### Health Check Tests
- `test_root_endpoint` - API root endpoint
- `test_docs_available` - Swagger documentation
- `test_openapi_spec` - OpenAPI specification

## Important Notes

- Tests use a real SQLite database (creates `lovable_dev.db`)
- Some tests may fail if `OPENAI_API_KEY` is not configured
- Tests create a mock user (ID: 1) for testing
- Database is not cleaned up between tests (for inspection)

## Continuous Integration

To integrate with CI/CD:

```yaml
# .github/workflows/test.yml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt pytest pytest-asyncio httpx
      - run: pytest backend/tests/
```
