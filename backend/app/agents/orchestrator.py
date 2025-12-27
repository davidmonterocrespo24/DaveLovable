from typing import List, Dict, Optional
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from app.agents.config import (
    llm_config,
    CODING_AGENT_SYSTEM_MESSAGE,
    UI_DESIGNER_AGENT_SYSTEM_MESSAGE,
    CODE_REVIEWER_AGENT_SYSTEM_MESSAGE,
    ARCHITECT_AGENT_SYSTEM_MESSAGE,
)
from app.core.config import settings
import json
import re


class AgentOrchestrator:
    """Orchestrates multiple AI agents using Microsoft AutoGen"""

    def __init__(self):
        self.llm_config = llm_config
        self.agents = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agents"""

        # Coding Agent - Generates code
        self.coding_agent = AssistantAgent(
            name="CodingAgent",
            system_message=CODING_AGENT_SYSTEM_MESSAGE,
            llm_config=self.llm_config,
        )

        # UI Designer Agent - Focuses on UI/UX
        self.ui_designer = AssistantAgent(
            name="UIDesigner",
            system_message=UI_DESIGNER_AGENT_SYSTEM_MESSAGE,
            llm_config=self.llm_config,
        )

        # Code Reviewer Agent - Reviews and improves code
        self.code_reviewer = AssistantAgent(
            name="CodeReviewer",
            system_message=CODE_REVIEWER_AGENT_SYSTEM_MESSAGE,
            llm_config=self.llm_config,
        )

        # Architect Agent - Designs system architecture
        self.architect = AssistantAgent(
            name="Architect",
            system_message=ARCHITECT_AGENT_SYSTEM_MESSAGE,
            llm_config=self.llm_config,
        )

        # User Proxy - Represents the user
        self.user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )

        self.agents = {
            "coding": self.coding_agent,
            "ui_designer": self.ui_designer,
            "code_reviewer": self.code_reviewer,
            "architect": self.architect,
        }

    def generate_code(self, user_request: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate code based on user request using agent collaboration

        Args:
            user_request: The user's request/prompt
            context: Optional context (existing files, project info, etc.)

        Returns:
            Dict with generated code and metadata
        """

        # Prepare context message
        context_msg = ""
        if context:
            context_msg = f"\n\nProject Context:\n{json.dumps(context, indent=2)}"

        full_message = f"{user_request}{context_msg}"

        # Create a group chat for collaborative code generation
        groupchat = GroupChat(
            agents=[
                self.user_proxy,
                self.architect,
                self.ui_designer,
                self.coding_agent,
                self.code_reviewer,
            ],
            messages=[],
            max_round=settings.AUTOGEN_MAX_ROUND,
            speaker_selection_method="round_robin",
        )

        manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

        # Start the conversation
        self.user_proxy.initiate_chat(manager, message=full_message)

        # Extract code from the conversation
        generated_code = self._extract_code_from_conversation(groupchat.messages)

        return {
            "code": generated_code,
            "messages": groupchat.messages,
            "success": len(generated_code) > 0,
        }

    def quick_code_generation(self, user_request: str, agent_type: str = "coding") -> str:
        """
        Quick code generation using a single agent

        Args:
            user_request: The user's request
            agent_type: Type of agent to use (coding, ui_designer, architect)

        Returns:
            Generated code as string
        """

        agent = self.agents.get(agent_type, self.coding_agent)

        # Create a simple conversation
        self.user_proxy.initiate_chat(
            agent,
            message=user_request,
            max_turns=2,
        )

        # Get the last message from the agent
        if hasattr(self.user_proxy, 'chat_messages') and agent.name in self.user_proxy.chat_messages:
            messages = self.user_proxy.chat_messages[agent.name]
            if messages:
                return self._extract_code_from_message(messages[-1].get('content', ''))

        return ""

    def review_code(self, code: str, context: Optional[str] = None) -> Dict:
        """
        Review existing code

        Args:
            code: The code to review
            context: Optional context about the code

        Returns:
            Dict with review feedback
        """

        message = f"Please review this code:\n\n```\n{code}\n```"
        if context:
            message += f"\n\nContext: {context}"

        self.user_proxy.initiate_chat(
            self.code_reviewer,
            message=message,
            max_turns=2,
        )

        # Extract feedback
        if hasattr(self.user_proxy, 'chat_messages') and self.code_reviewer.name in self.user_proxy.chat_messages:
            messages = self.user_proxy.chat_messages[self.code_reviewer.name]
            if messages:
                return {
                    "feedback": messages[-1].get('content', ''),
                    "success": True,
                }

        return {"feedback": "", "success": False}

    def _extract_code_from_conversation(self, messages: List[Dict]) -> List[Dict]:
        """Extract code blocks from conversation messages"""

        code_blocks = []

        for msg in messages:
            content = msg.get('content', '')
            code = self._extract_code_from_message(content)
            if code:
                code_blocks.extend(code)

        return code_blocks

    def _extract_code_from_message(self, message: str) -> List[Dict]:
        """Extract code blocks from a single message"""

        code_blocks = []

        # Pattern to match code blocks with optional language
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.finditer(pattern, message, re.DOTALL)

        for match in matches:
            language = match.group(1) or 'plaintext'
            code = match.group(2).strip()

            # Try to infer filename from code or context
            filename = self._infer_filename(code, language)

            code_blocks.append({
                'filename': filename,
                'language': language,
                'content': code,
            })

        return code_blocks

    def _infer_filename(self, code: str, language: str) -> str:
        """Infer filename from code content or language"""

        # Check for common patterns in code
        if 'export default App' in code or 'function App()' in code:
            return 'App.tsx'
        elif 'interface' in code or 'type ' in code:
            # Extract interface/type name
            match = re.search(r'(?:interface|type)\s+(\w+)', code)
            if match:
                return f"{match.group(1)}.tsx"
        elif language == 'css':
            return 'styles.css'
        elif language == 'json':
            return 'config.json'

        # Default naming based on language
        ext_map = {
            'typescript': 'ts',
            'tsx': 'tsx',
            'javascript': 'js',
            'jsx': 'jsx',
            'css': 'css',
            'html': 'html',
            'json': 'json',
        }

        ext = ext_map.get(language, 'txt')
        return f'generated.{ext}'


# Singleton instance
_orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the agent orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
