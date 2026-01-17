import json
import logging
from pathlib import Path
from typing import Sequence

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, TextMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_core.model_context import BufferedChatCompletionContext

from app.agents.prompts import (
    AGENT_SYSTEM_PROMPT,
    CODER_AGENT_DESCRIPTION,
    PLANNING_AGENT_DESCRIPTION,
    PLANNING_AGENT_SYSTEM_MESSAGE,
)
from app.core.gemini_client import Gemini3FlashChatCompletionClient
from app.agents.tools import (
    csv_info,
    delete_file,
    edit_file,
    file_search,
    filter_csv,
    glob_search,
    grep_search,
    json_get_value,
    json_to_text,
    list_dir,
    read_csv,
    read_file,
    read_json,
    run_terminal_cmd,
    validate_json,
    wiki_content,
    wiki_page_info,
    wiki_random,
    wiki_search,
    wiki_set_language,
    wiki_summary,
    write_file,
)
from app.agents.tools.csv_tools import merge_csv_files
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple AI agents using Microsoft AutoGen 0.4"""

    def __init__(self):
        # Terminate when Planner says "TERMINATE" or after 50 messages
        termination_condition = TextMentionTermination("TERMINATE") | MaxMessageTermination(50)

        self.coder_tools = [
            write_file,
            edit_file,
            delete_file,
            read_file,
            list_dir,
            file_search,
            glob_search,
            read_json,
            validate_json,
            json_get_value,
            json_to_text,
            read_csv,
            csv_info,
            filter_csv,
            wiki_search,
            wiki_summary,
            wiki_content,
            wiki_page_info,
            wiki_random,
            merge_csv_files,
            wiki_set_language,
            grep_search,
            run_terminal_cmd,
        ]

        # Create Gemini-3 Flash client with centralized configuration
        # Gemini-3 Flash Preview: 1M input tokens, 64K output tokens
        self.model_client = Gemini3FlashChatCompletionClient(
            temperature=0.7,
            max_tokens=64000,  # Gemini-3 Flash max output: 64K tokens
            parallel_tool_calls=False,  # Disable parallel tool calls to prevent token limit issues with large files
        )
        # Create buffered contexts with larger buffers to leverage Gemini's 1M input context
        # Keep last 100 messages (~50 exchanges) for richer context
        coder_context = BufferedChatCompletionContext(buffer_size=100)
        planner_context = BufferedChatCompletionContext(buffer_size=100)

        self.coder_agent = AssistantAgent(
            name="Coder",
            description=CODER_AGENT_DESCRIPTION,
            system_message=AGENT_SYSTEM_PROMPT,
            model_client=self.model_client,
            tools=self.coder_tools,  # Includes memory RAG tools
            max_tool_iterations=15,
            reflect_on_tool_use=False,
            model_context=coder_context,  # Limit context to prevent token overflow
        )

        # PlanningAgent (without tools, without memory)
        self.planning_agent = AssistantAgent(
            name="Planner",
            description=PLANNING_AGENT_DESCRIPTION,
            system_message=PLANNING_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client,
            tools=[],  # Planner has no tools, only plans
            model_context=planner_context,  # Limit context to prevent token overflow
        )

        def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
            # If no messages, start with Coder
            if not messages:
                return "Coder"

            last_message = messages[-1]
            logger.info(f"🔄 [Selector] Last message from: {last_message.source}, type: {type(last_message).__name__}")

            # CRITICAL: If Planner just spoke, it's ALWAYS Coder's turn (never terminate after Planner)
            if last_message.source == "Planner":
                logger.info("🔄 [Selector] Planner just spoke -> Selecting Coder (MANDATORY)")
                return "Coder"

            # If Coder just spoke
            if last_message.source == "Coder":
                # Check for explicit signals in TextMessage
                if isinstance(last_message, TextMessage):
                    if "TERMINATE" in last_message.content:
                        logger.info("🔄 [Selector] Coder said TERMINATE -> Ending conversation")
                        return None  # Let termination condition handle it
                    if "DELEGATE_TO_PLANNER" in last_message.content:
                        logger.info("🔄 [Selector] Coder delegating to Planner")
                        return "Planner"
                    if "SUBTASK_DONE" in last_message.content:
                        logger.info("🔄 [Selector] Coder subtask done -> Back to Planner")
                        return "Planner"

                # If Coder just sent a tool call (AssistantMessage with tool calls)
                # We usually want Coder to receive the result.
                # But here we assume the runtime executes the tool and appends the result.
                # We want to ensure Coder gets the next turn to read the result.
                logger.info("🔄 [Selector] Coder waiting for tool result -> Keep Coder")
                return "Coder"

            # If the last message was a tool execution result
            # (FunctionExecutionResultMessage usually has source='user' or the tool name, but definitely not 'Coder'/'Planner')
            # We must verify the type to be sure.
            if type(last_message).__name__ == "FunctionExecutionResultMessage":
                # Tool finished, give control back to Coder to handle the output
                logger.info("🔄 [Selector] Tool result received -> Back to Coder")
                return "Coder"

            # If the last message is from the User
            if last_message.source == "user":
                # Check for visual edit tag
                if "[VISUAL EDIT]" in last_message.content:
                    logger.info("🎨 [Selector] Visual Edit detected - Routing directly to Coder")
                    return "Coder"

                # Check for bug fix tag
                if "[BUG FIX]" in last_message.content:
                    logger.info("🐛 [Selector] Bug Fix detected - Routing directly to Coder")
                    return "Coder"

                # Default to Planner for normal requests
                logger.info("�� [Selector] User message -> Starting with Planner")
                return "Planner"

            # FALLBACK: Never return None unless we explicitly want to terminate
            # If we don't recognize the source, default to Coder to continue
            logger.warning(f"⚠️ [Selector] Unknown message source: {last_message.source} -> Defaulting to Coder")
            return "Coder"

        # Use SelectorGroupChat with custom selector
        self.main_team = SelectorGroupChat(
            participants=[self.coder_agent, self.planning_agent],
            model_client=self.model_client,
            termination_condition=termination_condition,
            selector_func=selector_func,
        )

    async def close(self):
        """Close the model client connection"""
        await self.model_client.close()

    async def save_state(self, project_id: int) -> None:
        """
        Save the state of the agent team to a JSON file in the project directory

        Args:
            project_id: The project ID to save state for
        """
        try:
            # Get project directory
            project_dir = Path(settings.PROJECTS_BASE_DIR) / f"project_{project_id}"
            project_dir.mkdir(parents=True, exist_ok=True)

            # Save team state
            team_state = await self.main_team.save_state()

            # Save to JSON file
            state_file = project_dir / ".agent_state.json"
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(team_state, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Saved agent state for project {project_id} to {state_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save agent state for project {project_id}: {e}")
            # Don't raise - state saving is optional

    async def load_state(self, project_id: int) -> bool:
        """
        Load the state of the agent team from a JSON file in the project directory.
        Automatically truncates old messages to prevent token overflow.

        Args:
            project_id: The project ID to load state for

        Returns:
            True if state was loaded successfully, False otherwise
        """
        try:
            # Get state file path
            state_file = Path(settings.PROJECTS_BASE_DIR) / f"project_{project_id}" / ".agent_state.json"

            if not state_file.exists():
                logger.info(f"ℹ️  No saved state found for project {project_id}")
                return False

            # Load state from file
            with open(state_file, "r", encoding="utf-8") as f:
                team_state = json.load(f)

            # CRITICAL: Truncate message history to prevent token overflow
            # With Gemini-3 Flash's 1M input tokens, we can keep more history
            # Keep only the last 150 messages from the saved state (~75 exchanges)
            if "message_thread" in team_state and isinstance(team_state["message_thread"], list):
                original_count = len(team_state["message_thread"])
                if original_count > 150:
                    # Keep last 150 messages
                    team_state["message_thread"] = team_state["message_thread"][-150:]
                    logger.warning(
                        f"⚠️  Truncated message history from {original_count} to {len(team_state['message_thread'])} messages to prevent token overflow"
                    )
                else:
                    logger.info(f"ℹ️  Loading {original_count} messages from saved state")

            # Load state into team
            await self.main_team.load_state(team_state)

            logger.info(f"✅ Loaded agent state for project {project_id} from {state_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load agent state for project {project_id}: {e}")
            return False


import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional


class OrchestratorManager:
    """Manages orchestrator instances per project with automatic cleanup after inactivity"""

    def __init__(self, inactivity_timeout: int = 1200):  # 20 minutes = 1200 seconds
        self._orchestrators: Dict[int, tuple[AgentOrchestrator, datetime]] = {}
        self._locks: Dict[int, asyncio.Lock] = {}
        self._inactivity_timeout = inactivity_timeout
        self._cleanup_task: Optional[asyncio.Task] = None

    async def get_orchestrator(self, project_id: int) -> AgentOrchestrator:
        """Get or create an orchestrator instance for a specific project"""
        # Create lock for this project if it doesn't exist
        if project_id not in self._locks:
            self._locks[project_id] = asyncio.Lock()

        async with self._locks[project_id]:
            # Update last access time if orchestrator exists
            if project_id in self._orchestrators:
                orchestrator, _ = self._orchestrators[project_id]
                self._orchestrators[project_id] = (orchestrator, datetime.now())
                logger.info(f"♻️  Reusing existing orchestrator for project {project_id}")
                return orchestrator

            # Create new orchestrator for this project
            logger.info(f"🆕 Creating new orchestrator instance for project {project_id}")
            orchestrator = AgentOrchestrator()

            # Try to load saved state
            state_loaded = await orchestrator.load_state(project_id)
            if state_loaded:
                logger.info(f"✅ Loaded saved state for project {project_id}")

            # Store with current timestamp
            self._orchestrators[project_id] = (orchestrator, datetime.now())

            # Start cleanup task if not running
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_inactive_orchestrators())

            return orchestrator

    async def release_orchestrator(self, project_id: int) -> None:
        """Manually release an orchestrator and save its state"""
        if project_id not in self._locks:
            return

        async with self._locks[project_id]:
            if project_id in self._orchestrators:
                orchestrator, _ = self._orchestrators[project_id]
                logger.info(f"💾 Saving state for project {project_id} before release")
                await orchestrator.save_state(project_id)
                await orchestrator.close()
                del self._orchestrators[project_id]
                logger.info(f"🗑️  Released orchestrator for project {project_id}")

    async def _cleanup_inactive_orchestrators(self) -> None:
        """Background task to cleanup inactive orchestrators"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                now = datetime.now()
                inactive_projects = []

                # Find inactive projects
                for project_id, (orchestrator, last_access) in list(self._orchestrators.items()):
                    if now - last_access > timedelta(seconds=self._inactivity_timeout):
                        inactive_projects.append(project_id)

                # Cleanup inactive projects
                for project_id in inactive_projects:
                    logger.info(f"⏰ Project {project_id} inactive for {self._inactivity_timeout}s, cleaning up...")
                    await self.release_orchestrator(project_id)

            except Exception as e:
                logger.error(f"❌ Error in orchestrator cleanup task: {e}")
                await asyncio.sleep(60)  # Continue trying

    async def shutdown(self) -> None:
        """Shutdown all orchestrators and save their states"""
        logger.info("🛑 Shutting down all orchestrators...")
        for project_id in list(self._orchestrators.keys()):
            await self.release_orchestrator(project_id)
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# Global orchestrator manager instance
_manager = OrchestratorManager()


async def get_orchestrator(project_id: int) -> AgentOrchestrator:
    """Get or create an orchestrator instance for a specific project"""
    return await _manager.get_orchestrator(project_id)


async def release_orchestrator(project_id: int) -> None:
    """Release an orchestrator instance and save its state"""
    await _manager.release_orchestrator(project_id)


async def shutdown_orchestrators() -> None:
    """Shutdown all orchestrators gracefully"""
    await _manager.shutdown()
