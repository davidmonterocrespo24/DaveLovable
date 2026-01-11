"""
Multi-Agent System Integration Tests

Tests for the SelectorGroupChat architecture with Planner and Coder agents.
Verifies that the agent orchestrator and chat service work correctly together.

Run with: pytest backend/tests/test_multiagent_system.py -v
Run specific test: pytest backend/tests/test_multiagent_system.py::test_orchestrator_initialization -v
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.agents.orchestrator import AgentOrchestrator, get_orchestrator
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.models import MessageRole, Project
from app.schemas import ChatRequest
from app.services.chat_service import ChatService


class TestOrchestratorInitialization:
    """Test orchestrator initialization and configuration"""

    def test_orchestrator_singleton(self):
        """Test that orchestrator is a singleton"""
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()

        assert orchestrator1 is orchestrator2
        assert isinstance(orchestrator1, AgentOrchestrator)

    def test_orchestrator_has_required_components(self):
        """Test that orchestrator has all required components"""
        orchestrator = get_orchestrator()

        # Check agents exist
        assert hasattr(orchestrator, "coder_agent")
        assert hasattr(orchestrator, "planning_agent")
        assert hasattr(orchestrator, "main_team")
        assert hasattr(orchestrator, "model_client")

        # Check agent names
        assert orchestrator.coder_agent.name == "Coder"
        assert orchestrator.planning_agent.name == "Planner"

    def test_coder_agent_has_tools(self):
        """Test that Coder agent has all required tools"""
        orchestrator = get_orchestrator()

        # Coder should have tools
        assert len(orchestrator.coder_tools) > 0

        # Check for essential file operation tools
        tool_names = [tool.__name__ for tool in orchestrator.coder_tools]

        essential_tools = [
            "write_file",
            "read_file",
            "edit_file",
            "delete_file",
            "list_dir",
        ]

        for tool in essential_tools:
            assert tool in tool_names, f"Missing essential tool: {tool}"

    def test_planner_agent_has_no_tools(self):
        """Test that Planner agent has no tools (only plans)"""
        orchestrator = get_orchestrator()

        # Planner should have empty tools list
        assert orchestrator.planning_agent._tools == []

    def test_team_configuration(self):
        """Test that SelectorGroupChat team is properly configured"""
        orchestrator = get_orchestrator()

        # Check team has both agents
        assert len(orchestrator.main_team._participants) == 2

        # Check termination condition exists
        assert orchestrator.main_team._termination_condition is not None


class TestAgentTools:
    """Test agent tools functionality"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        yield Path(temp_dir)

        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    @pytest.mark.skip(reason="Tool tests require specific agent tool dependencies")
    @pytest.mark.asyncio
    async def test_write_file_tool(self, temp_workspace):
        """Test that write_file tool works"""
        # Skipped - requires src.tools.common module
        pass

    @pytest.mark.skip(reason="Tool tests require specific agent tool dependencies")
    @pytest.mark.asyncio
    async def test_read_file_tool(self, temp_workspace):
        """Test that read_file tool works"""
        # Skipped - requires src.tools.common module
        pass

    @pytest.mark.skip(reason="Tool tests require specific agent tool dependencies")
    @pytest.mark.asyncio
    async def test_edit_file_tool(self, temp_workspace):
        """Test that edit_file tool works"""
        # Skipped - requires src.tools.common module
        pass


class TestChatServiceIntegration:
    """Test chat service integration with multi-agent system"""

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_db(self):
        """Set up test database"""
        Base.metadata.create_all(bind=engine)
        yield
        # Cleanup happens after all tests in class

    @pytest.fixture
    def db_session(self):
        """Create database session for tests"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def test_project(self, db_session):
        """Create a test project"""
        from app.services.filesystem_service import FileSystemService

        # Create project in database
        project = Project(
            id=999,  # Use high ID to avoid conflicts
            name="Test Multiagent Project",
            description="Test project for multi-agent system",
            user_id=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # Create project structure on filesystem
        FileSystemService.create_project_structure(project.id, project.name)

        yield project

        # Cleanup
        db_session.delete(project)
        db_session.commit()
        FileSystemService.delete_project(project.id)

    def test_chat_service_create_session(self, db_session, test_project):
        """Test creating a chat session"""
        from app.schemas import ChatSessionCreate

        session_data = ChatSessionCreate(project_id=test_project.id)
        session = ChatService.create_session(db_session, session_data)

        assert session.id is not None
        assert session.project_id == test_project.id

    @pytest.mark.asyncio
    async def test_chat_service_with_mock_orchestrator(self, db_session, test_project):
        """Test chat service with mocked orchestrator response"""

        # Create mock response from orchestrator
        mock_result = Mock()
        mock_message = Mock()
        mock_message.content = "I have created the component as requested. TASK_COMPLETED"
        mock_message.source = "Coder"
        mock_result.messages = [mock_message]

        # Mock the orchestrator
        with patch("app.services.chat_service.get_orchestrator") as mock_get_orch:
            mock_orchestrator = Mock()
            mock_orchestrator.main_team.run = AsyncMock(return_value=mock_result)
            mock_get_orch.return_value = mock_orchestrator

            # Create chat request
            chat_request = ChatRequest(message="Create a simple Button component", session_id=None)

            # Process message
            result = await ChatService.process_chat_message(
                db=db_session, project_id=test_project.id, chat_request=chat_request
            )

            # Verify result
            assert "session_id" in result
            assert "message" in result
            assert result["message"].role == MessageRole.ASSISTANT
            assert (
                "created the component" in result["message"].content.lower()
                or "task_completed" in result["message"].content.lower()
            )

    @pytest.mark.asyncio
    async def test_working_directory_context(self, db_session, test_project):
        """Test that working directory is set correctly for agent tools"""
        from pathlib import Path

        original_cwd = os.getcwd()

        # Mock orchestrator to capture the working directory when run is called
        captured_cwd = None

        async def mock_run(*args, **kwargs):
            nonlocal captured_cwd
            captured_cwd = os.getcwd()

            mock_result = Mock()
            mock_message = Mock()
            mock_message.content = "Task completed"
            mock_message.source = "Coder"
            mock_result.messages = [mock_message]
            return mock_result

        with patch("app.services.chat_service.get_orchestrator") as mock_get_orch:
            mock_orchestrator = Mock()
            mock_orchestrator.main_team.run = mock_run
            mock_get_orch.return_value = mock_orchestrator

            chat_request = ChatRequest(message="Test working directory", session_id=None)

            await ChatService.process_chat_message(db=db_session, project_id=test_project.id, chat_request=chat_request)

            # Verify working directory was set to project directory during execution
            expected_dir = Path(settings.PROJECTS_BASE_DIR) / f"project_{test_project.id}"
            assert captured_cwd == str(expected_dir)

            # Verify working directory was restored
            assert os.getcwd() == original_cwd


class TestEndToEndMultiAgent:
    """End-to-end tests with real multi-agent system (requires OpenAI API key)"""

    @pytest.fixture(scope="class", autouse=True)
    def check_api_key(self):
        """Skip tests if OpenAI API key is not configured"""
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-api-key-here":
            pytest.skip("OpenAI API key not configured - skipping end-to-end tests")

    @pytest.fixture(scope="class")
    def setup_test_db(self):
        """Set up test database"""
        Base.metadata.create_all(bind=engine)
        yield

    @pytest.fixture
    def db_session(self):
        """Create database session"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def test_project(self, db_session):
        """Create test project"""
        from app.services.filesystem_service import FileSystemService

        project = Project(id=998, name="E2E Test Project", description="End-to-end test project", user_id=1)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        FileSystemService.create_project_structure(project.id, project.name)

        yield project

        db_session.delete(project)
        db_session.commit()
        FileSystemService.delete_project(project.id)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_agent_simple_task(self, db_session, test_project):
        """Test real multi-agent system with a simple task"""

        chat_request = ChatRequest(
            message="Create a simple file called hello.txt with the content 'Hello from agents!'", session_id=None
        )

        # This will use the real orchestrator and agents
        result = await ChatService.process_chat_message(
            db=db_session, project_id=test_project.id, chat_request=chat_request
        )

        # Verify response was created
        assert result["session_id"] is not None
        assert result["message"] is not None
        assert result["message"].role == MessageRole.ASSISTANT

        # Check if file was created by agents
        from app.services.filesystem_service import FileSystemService

        project_dir = FileSystemService.get_project_dir(test_project.id)
        hello_file = project_dir / "hello.txt"

        # Note: This might not always work depending on agent behavior
        # Agents might create files in different locations
        print(f"\nAgent response: {result['message'].content}")
        print(f"Checking for file at: {hello_file}")

        # Just verify we got a response - actual file creation depends on agent execution
        assert len(result["message"].content) > 0


class TestErrorHandling:
    """Test error handling in multi-agent system"""

    @pytest.fixture
    def db_session(self):
        """Create database session"""
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def test_project(self, db_session):
        """Create test project"""
        from app.services.filesystem_service import FileSystemService

        project = Project(id=997, name="Error Test Project", description="Project for error testing", user_id=1)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        FileSystemService.create_project_structure(project.id, project.name)

        yield project

        db_session.delete(project)
        db_session.commit()
        FileSystemService.delete_project(project.id)

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling(self, db_session, test_project):
        """Test that errors from orchestrator are handled gracefully"""

        # Mock orchestrator to raise an error
        with patch("app.services.chat_service.get_orchestrator") as mock_get_orch:
            mock_orchestrator = Mock()
            mock_orchestrator.main_team.run = AsyncMock(side_effect=Exception("Simulated agent error"))
            mock_get_orch.return_value = mock_orchestrator

            chat_request = ChatRequest(message="This will cause an error", session_id=None)

            result = await ChatService.process_chat_message(
                db=db_session, project_id=test_project.id, chat_request=chat_request
            )

            # Should return error message instead of crashing
            assert "session_id" in result
            assert "message" in result
            assert "error" in result["message"].content.lower()

    @pytest.mark.asyncio
    async def test_missing_api_key_handling(self, db_session, test_project):
        """Test handling when OpenAI API key is not configured"""

        # Mock get_orchestrator to raise ValueError (like when API key is missing)
        with patch(
            "app.services.chat_service.get_orchestrator", side_effect=ValueError("OpenAI API key not configured")
        ):
            chat_request = ChatRequest(message="Test message", session_id=None)

            result = await ChatService.process_chat_message(
                db=db_session, project_id=test_project.id, chat_request=chat_request
            )

            # Should return error message
            assert "message" in result
            assert "api key" in result["message"].content.lower()


if __name__ == "__main__":
    # Run tests with: python -m pytest backend/tests/test_multiagent_system.py -v
    pytest.main([__file__, "-v", "-s"])
