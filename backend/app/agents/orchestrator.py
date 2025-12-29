from typing import List, Dict, Optional, Sequence
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage, BaseAgentEvent, BaseChatMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from app.agents.prompts import (
    AGENT_SYSTEM_PROMPT,
    CODER_AGENT_DESCRIPTION,
    PLANNING_AGENT_DESCRIPTION,
    PLANNING_AGENT_SYSTEM_MESSAGE,
)

from app.agents.tools import (
    read_file,
    write_file,
    edit_file,
    delete_file,
    list_dir,
    glob_search,
    grep_search,
    file_search,
    run_terminal_cmd,
    read_json,
    write_json,
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
    wiki_set_language,
)
from app.core.config import settings
from app.agents.tools.csv_tools import merge_csv_files
import json
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple AI agents using Microsoft AutoGen 0.4"""

    def __init__(self):
        # Terminate when Planner says "TERMINATE" or after 50 messages
        termination_condition = TextMentionTermination(
            "TERMINATE"
        ) | MaxMessageTermination(50)
        
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
        model_info = {
                    "vision": True,
                    "function_calling": True,
                    "json_output": True,
                    "family": "unknown",
                    "structured_output": True,
                }

        self.model_client = OpenAIChatCompletionClient(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE_URL,
            temperature=0.7,
            model_info=model_info,
        )
        self.coder_agent = AssistantAgent(
            name="Coder",
            description=CODER_AGENT_DESCRIPTION,
            system_message=AGENT_SYSTEM_PROMPT,
            model_client=self.model_client ,
            tools=self.coder_tools,  # Includes memory RAG tools
            max_tool_iterations=15,
            reflect_on_tool_use=False,
            # NO memory parameter - uses RAG tools instead
        )

        # PlanningAgent (without tools, without memory)
        self.planning_agent = AssistantAgent(
            name="Planner",
            description=PLANNING_AGENT_DESCRIPTION,
            system_message=PLANNING_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client,
            tools=[],  # Planner has no tools, only plans
            # NO memory parameter
        )

        def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
            # If no messages, start with Planner
            if not messages:
                return "Planner"
            
            last_message = messages[-1]
            
            # If Planner just spoke, it's Coder's turn to execute the task
            if last_message.source == "Planner":
                return "Coder"
                
            # If Coder just spoke
            if last_message.source == "Coder":
                # Check if Coder checked off the task with SUBTASK_DONE
                if isinstance(last_message, TextMessage) and "SUBTASK_DONE" in last_message.content:
                    return "Planner"
                # If just tool usage or partial response, Coder keeps going
                return "Coder"
                
            return None

        # Use SelectorGroupChat with custom selector
        self.main_team = SelectorGroupChat(
            participants=[self.planning_agent, self.coder_agent],
            model_client=self.model_client, # Required for SelectorGroupChat
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
        Load the state of the agent team from a JSON file in the project directory

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

            # Load state into team
            await self.main_team.load_state(team_state)

            logger.info(f"✅ Loaded agent state for project {project_id} from {state_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load agent state for project {project_id}: {e}")
            return False

    async def reset_state(self, project_id: int) -> None:
        """
        Reset the agent team state and delete the saved state file

        Args:
            project_id: The project ID to reset state for
        """
        try:
            # Reset team state
            await self.main_team.reset()

            # Delete state file if it exists
            state_file = Path(settings.PROJECTS_BASE_DIR) / f"project_{project_id}" / ".agent_state.json"
            if state_file.exists():
                state_file.unlink()
                logger.info(f"✅ Deleted agent state file for project {project_id}")

            logger.info(f"✅ Reset agent state for project {project_id}")

        except Exception as e:
            logger.error(f"❌ Failed to reset agent state for project {project_id}: {e}")


# Singleton instance
_orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the agent orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
