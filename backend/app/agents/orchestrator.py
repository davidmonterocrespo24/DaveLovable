from typing import List, Dict, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from app.agents.prompts import (
    AGENT_SYSTEM_PROMPT,
    CODER_AGENT_DESCRIPTION,
    PLANNING_AGENT_DESCRIPTION,
    PLANNING_AGENT_SYSTEM_MESSAGE,
)

from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination

# Imports added for the new flow
from autogen_agentchat.teams import SelectorGroupChat
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


class AgentOrchestrator:
    """Orchestrates multiple AI agents using Microsoft AutoGen 0.4"""

    def __init__(self):
        # Terminate when agent says "TASK_COMPLETED" or after 50 messages
        termination_condition = TextMentionTermination(
            "TASK_COMPLETED"
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
            max_tool_iterations=25,
            reflect_on_tool_use=False,
            # NO memory parameter - uses RAG tools instead
        )

        # PlanningAgent (without tools, without memory)
        self.planning_agent = AssistantAgent(
            name="Planner",
            description=PLANNING_AGENT_DESCRIPTION,
            system_message=PLANNING_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client ,
            tools=[],  # Planner has no tools, only plans
            # NO memory parameter
        )
        self.main_team = SelectorGroupChat(
            participants=[self.planning_agent, self.coder_agent],
            model_client=self.model_client,
            termination_condition=termination_condition,
            allow_repeated_speaker=True,  # Allows the same agent to speak multiple times
        )

    async def close(self):
        """Close the model client connection"""
        await self.model_client.close()


# Singleton instance
_orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the agent orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
