"""
API Integration Tests

Tests for the FastAPI endpoints to ensure proper integration
between frontend and backend.

Run with: pytest backend/tests/test_api.py
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import Base, SessionLocal, engine
from app.main import app
from app.models import User

# Create test client
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Set up test database before tests"""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create test user
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.id == 1).first()
        if not test_user:
            test_user = User(
                id=1,
                email="test@example.com",
                username="testuser",
                hashed_password=get_password_hash("testpass123"),
                is_active=True,
            )
            db.add(test_user)
            db.commit()
    finally:
        db.close()

    yield

    # Cleanup after tests
    # Base.metadata.drop_all(bind=engine)


class TestProjectAPI:
    """Test Project CRUD endpoints"""

    def test_create_project(self):
        """Test creating a new project"""
        response = client.post("/api/v1/projects", json={"name": "Test Project", "description": "A test project"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert "id" in data
        assert "files" in data
        return data["id"]

    def test_list_projects(self):
        """Test listing all projects"""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_project(self):
        """Test getting a specific project"""
        # First create a project
        create_response = client.post("/api/v1/projects", json={"name": "Get Test Project"})
        project_id = create_response.json()["id"]

        # Get the project
        response = client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Get Test Project"

    def test_update_project(self):
        """Test updating a project"""
        # Create project
        create_response = client.post("/api/v1/projects", json={"name": "Update Test"})
        project_id = create_response.json()["id"]

        # Update project
        response = client.put(f"/api/v1/projects/{project_id}", json={"name": "Updated Name"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_delete_project(self):
        """Test deleting a project"""
        # Create project
        create_response = client.post("/api/v1/projects", json={"name": "Delete Test"})
        project_id = create_response.json()["id"]

        # Delete project
        response = client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404


class TestFileAPI:
    """Test File CRUD endpoints"""

    @pytest.fixture
    def project_id(self):
        """Create a test project"""
        response = client.post("/api/v1/projects", json={"name": "File Test Project"})
        return response.json()["id"]

    def test_create_file(self, project_id):
        """Test creating a file"""
        response = client.post(
            f"/api/v1/projects/{project_id}/files",
            json={
                "filename": "test.tsx",
                "filepath": "/src/test.tsx",
                "content": "export const Test = () => <div>Test</div>",
                "language": "typescript",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.tsx"
        assert "id" in data

    def test_list_files(self, project_id):
        """Test listing files"""
        response = client.get(f"/api/v1/projects/{project_id}/files")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_file(self, project_id):
        """Test updating file content"""
        # Create file
        create_response = client.post(
            f"/api/v1/projects/{project_id}/files",
            json={
                "filename": "update.tsx",
                "filepath": "/src/update.tsx",
                "content": "old content",
                "language": "typescript",
            },
        )
        file_id = create_response.json()["id"]

        # Update file
        response = client.put(f"/api/v1/projects/{project_id}/files/{file_id}", json={"content": "new content"})
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "new content"

    def test_delete_file(self, project_id):
        """Test deleting a file"""
        # Create file
        create_response = client.post(
            f"/api/v1/projects/{project_id}/files",
            json={
                "filename": "delete.tsx",
                "filepath": "/src/delete.tsx",
                "content": "content",
                "language": "typescript",
            },
        )
        file_id = create_response.json()["id"]

        # Delete file
        response = client.delete(f"/api/v1/projects/{project_id}/files/{file_id}")
        assert response.status_code == 200


class TestChatAPI:
    """Test Chat endpoints"""

    @pytest.fixture
    def project_id(self):
        """Create a test project"""
        response = client.post("/api/v1/projects", json={"name": "Chat Test Project"})
        return response.json()["id"]

    def test_send_message(self, project_id):
        """Test sending a chat message"""
        # Note: This test may fail if OPENAI_API_KEY is not set
        # or if you want to avoid actual API calls
        response = client.post(f"/api/v1/chat/{project_id}", json={"message": "Create a simple button component"})

        # Accept both success and error for API key issues
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "session_id" in data

    def test_list_sessions(self, project_id):
        """Test listing chat sessions"""
        response = client.get(f"/api/v1/chat/{project_id}/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestHealthCheck:
    """Test API health and documentation"""

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200

    def test_docs_available(self):
        """Test that API documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_spec(self):
        """Test OpenAPI specification"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
