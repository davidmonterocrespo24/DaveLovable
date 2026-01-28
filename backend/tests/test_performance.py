"""
Performance test for /projects endpoint

This test verifies that the performance optimizations (indexes and eager loading)
are working correctly and that response times are acceptable.

Run with: pytest backend/tests/test_performance.py -v
"""

import time
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
    """Set up test database with sample data"""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create test user
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.id == 1).first()
        if not test_user:
            test_user = User(
                id=1,
                email="perf@test.com",
                username="perfuser",
                hashed_password=get_password_hash("testpass123"),
                is_active=True,
            )
            db.add(test_user)
            db.commit()
    finally:
        db.close()

    # Create multiple test projects to test performance with volume
    print("\n📊 Creating test projects for performance testing...")
    for i in range(20):
        client.post(
            "/api/v1/projects",
            json={
                "name": f"Performance Test Project {i+1}",
                "description": f"Test project {i+1} for performance testing"
            }
        )
    print("✅ Test projects created")

    yield

    # Cleanup would go here if needed


class TestProjectsPerformance:
    """Test performance of /projects endpoint"""

    def test_list_projects_response_time(self):
        """Test that listing projects responds quickly"""
        # Warm up
        client.get("/api/v1/projects")
        
        # Measure response time
        start_time = time.time()
        response = client.get("/api/v1/projects")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Performance assertion - should be fast (< 500ms for 20+ projects)
        print(f"\n⏱️  Response time: {response_time_ms:.2f}ms")
        assert response_time_ms < 500, f"Response too slow: {response_time_ms:.2f}ms"
        
        # Log performance metrics
        print(f"📈 Projects returned: {len(data)}")
        print(f"📊 Avg time per project: {response_time_ms / len(data):.2f}ms")

    def test_list_projects_no_lazy_loading(self):
        """Verify that projects are returned without lazy loading issues"""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify that basic project fields are present
        for project in data:
            assert "id" in project
            assert "name" in project
            assert "description" in project
            assert "owner_id" in project
            assert "created_at" in project
            assert "updated_at" in project
            
            # Files and chat_sessions should NOT be in the response
            # (we use noload to prevent them from being fetched)
            # The schema doesn't include them in List[Project] response
            assert "files" not in project or project.get("files") is None
            assert "chat_sessions" not in project or project.get("chat_sessions") is None

    def test_pagination_performance(self):
        """Test that pagination works correctly and performs well"""
        # Test with limit
        start_time = time.time()
        response = client.get("/api/v1/projects?limit=10")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
        
        print(f"\n⏱️  Paginated response time (limit=10): {response_time_ms:.2f}ms")
        assert response_time_ms < 200, f"Paginated response too slow: {response_time_ms:.2f}ms"

    def test_multiple_requests_performance(self):
        """Test that multiple sequential requests perform well"""
        times = []
        
        # Make 5 requests and measure each
        for i in range(5):
            start_time = time.time()
            response = client.get("/api/v1/projects")
            end_time = time.time()
            
            assert response.status_code == 200
            times.append((end_time - start_time) * 1000)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\n📊 Average response time (5 requests): {avg_time:.2f}ms")
        print(f"📊 Max response time: {max_time:.2f}ms")
        print(f"📊 Min response time: {min(times):.2f}ms")
        
        # Average should be good
        assert avg_time < 500, f"Average response time too high: {avg_time:.2f}ms"
        # No single request should be extremely slow
        assert max_time < 1000, f"Max response time too high: {max_time:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
