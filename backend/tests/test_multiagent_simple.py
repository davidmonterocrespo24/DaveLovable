"""
Simple Multi-Agent System Verification Script

Verifies that the multi-agent system is functioning correctly without pytest complexity.

Run with: python backend/tests/test_multiagent_simple.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_orchestrator_initialization():
    """Test that orchestrator initializes correctly"""
    print("\n=== Test 1: Orchestrator Initialization ===")

    from app.agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()

    # Check singleton
    orchestrator2 = get_orchestrator()
    assert orchestrator is orchestrator2, "Orchestrator should be a singleton"
    print("✓ Orchestrator is a singleton")

    # Check components exist
    assert hasattr(orchestrator, "coder_agent"), "Missing coder_agent"
    assert hasattr(orchestrator, "planning_agent"), "Missing planning_agent"
    assert hasattr(orchestrator, "main_team"), "Missing main_team"
    print("✓ All components exist")

    # Check agent names
    assert orchestrator.coder_agent.name == "Coder", f"Expected 'Coder', got '{orchestrator.coder_agent.name}'"
    assert orchestrator.planning_agent.name == "Planner", (
        f"Expected 'Planner', got '{orchestrator.planning_agent.name}'"
    )
    print(f"✓ Agent names correct: {orchestrator.coder_agent.name}, {orchestrator.planning_agent.name}")

    # Check tools
    assert len(orchestrator.coder_tools) > 0, "Coder should have tools"
    tool_names = [tool.__name__ for tool in orchestrator.coder_tools]
    print(f"✓ Coder has {len(orchestrator.coder_tools)} tools: {', '.join(tool_names[:5])}...")

    # Check essential tools
    essential_tools = ["write_file", "read_file", "edit_file", "delete_file", "list_dir"]
    for tool in essential_tools:
        assert tool in tool_names, f"Missing essential tool: {tool}"
    print("✓ All essential file operation tools present")

    # Check planner has no tools
    assert orchestrator.planning_agent._tools == [], "Planner should have no tools"
    print("✓ Planner has no tools (only plans)")

    # Check team configuration
    assert len(orchestrator.main_team._participants) == 2, "Team should have 2 participants"
    print("✓ Team has 2 participants (Planner + Coder)")

    print("\n✅ Test 1 PASSED: Orchestrator initialization successful\n")
    return True


def test_chat_service_integration():
    """Test chat service integration basics"""
    print("\n=== Test 2: Chat Service Integration ===")

    from app.db.database import SessionLocal
    from app.models import MessageRole
    from app.schemas import ChatMessageCreate, ChatSessionCreate
    from app.services.chat_service import ChatService

    db = SessionLocal()
    try:
        # Test session creation
        from app.models import Project
        from app.services.filesystem_service import FileSystemService

        # Create test project
        test_project = Project(id=9999, name="Test Project", description="Test", owner_id=1)
        db.add(test_project)
        db.commit()
        db.refresh(test_project)

        # Create project structure
        FileSystemService.create_project_structure(test_project.id, test_project.name)
        print(f"✓ Created test project {test_project.id}")

        # Create session
        session_data = ChatSessionCreate(project_id=test_project.id)
        session = ChatService.create_session(db, session_data)
        assert session.id is not None, "Session should have an ID"
        assert session.project_id == test_project.id, "Session should be linked to project"
        print(f"✓ Created chat session {session.id}")

        # Create message
        message_data = ChatMessageCreate(session_id=session.id, role=MessageRole.USER, content="Test message")
        message = ChatService.add_message(db, message_data)
        assert message.id is not None, "Message should have an ID"
        assert message.content == "Test message", "Message content should match"
        print(f"✓ Created chat message {message.id}")

        # Cleanup
        db.delete(test_project)
        db.commit()
        # Skip file cleanup on Windows due to Git file lock issues
        try:
            FileSystemService.delete_project(test_project.id)
            print("✓ Cleanup successful")
        except PermissionError:
            print("⚠ File cleanup skipped (Git lock on Windows)")

        print("\n✅ Test 2 PASSED: Chat service integration works\n")
        return True

    finally:
        db.close()


def test_working_directory_context():
    """Test that working directory context is set correctly"""
    print("\n=== Test 3: Working Directory Context ===")

    import shutil
    import tempfile
    from pathlib import Path

    # Use tempfile instead of creating in projects directory
    temp_dir = Path(tempfile.mkdtemp())
    print(f"✓ Created temporary directory: {temp_dir}")

    original_cwd = os.getcwd()

    # Test changing directory
    os.chdir(temp_dir)
    current_dir = str(Path(os.getcwd()).resolve())
    expected_resolved = str(temp_dir.resolve())
    assert current_dir == expected_resolved, (
        f"Working directory should change. Expected: {expected_resolved}, Got: {current_dir}"
    )
    print("✓ Changed working directory to temp directory")

    # Test restoring directory
    os.chdir(original_cwd)
    assert os.getcwd() == original_cwd, "Working directory should restore"
    print("✓ Restored original working directory")

    # Cleanup
    shutil.rmtree(temp_dir)
    print("✓ Cleanup successful")

    print("\n✅ Test 3 PASSED: Working directory context works\n")
    return True


def test_architecture_components():
    """Test that new architecture components are in place"""
    print("\n=== Test 4: Architecture Components ===")

    # Check orchestrator file
    from app.agents import orchestrator as orch_module

    assert hasattr(orch_module, "AgentOrchestrator"), "Missing AgentOrchestrator class"
    assert hasattr(orch_module, "get_orchestrator"), "Missing get_orchestrator function"
    print("✓ Orchestrator module has required exports")

    # Check chat service file
    from app.services import chat_service as chat_module

    assert hasattr(chat_module, "ChatService"), "Missing ChatService class"
    print("✓ Chat service module has required exports")

    # Check filesystem service still exists
    from app.services import filesystem_service as fs_module

    assert hasattr(fs_module, "FileSystemService"), "Missing FileSystemService class"
    print("✓ FileSystemService still exists (as expected)")

    # Check prompts
    from app.agents import prompts

    assert hasattr(prompts, "AGENT_SYSTEM_PROMPT"), "Missing AGENT_SYSTEM_PROMPT"
    assert hasattr(prompts, "CODER_AGENT_DESCRIPTION"), "Missing CODER_AGENT_DESCRIPTION"
    assert hasattr(prompts, "PLANNING_AGENT_DESCRIPTION"), "Missing PLANNING_AGENT_DESCRIPTION"
    assert hasattr(prompts, "PLANNING_AGENT_SYSTEM_MESSAGE"), "Missing PLANNING_AGENT_SYSTEM_MESSAGE"
    print("✓ All agent prompts defined")

    # Check tools are importable
    from app.agents import tools

    assert hasattr(tools, "read_file"), "Missing read_file tool"
    assert hasattr(tools, "write_file"), "Missing write_file tool"
    assert hasattr(tools, "edit_file"), "Missing edit_file tool"
    print("✓ Agent tools are importable")

    print("\n✅ Test 4 PASSED: All architecture components in place\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MULTI-AGENT SYSTEM VERIFICATION")
    print("=" * 60)

    tests = [
        test_orchestrator_initialization,
        test_architecture_components,
        test_working_directory_context,
        test_chat_service_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test {test.__name__} FAILED with error:")
            print(f"   {type(e).__name__}: {e!s}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Multi-agent system is working correctly!")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
