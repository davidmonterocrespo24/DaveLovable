from typing import List, Dict, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from app.agents.config import (
    CODING_AGENT_SYSTEM_MESSAGE,
    UI_DESIGNER_AGENT_SYSTEM_MESSAGE,
    CODE_REVIEWER_AGENT_SYSTEM_MESSAGE,
    ARCHITECT_AGENT_SYSTEM_MESSAGE,
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
)
from app.core.config import settings
import json
import re


class AgentOrchestrator:
    """Orchestrates multiple AI agents using Microsoft AutoGen 0.4"""

    def __init__(self):
        # Check if API key is configured
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
            raise ValueError(
                "OpenAI API key is not configured. Please set OPENAI_API_KEY in your .env file. "
                "You can get an API key from your LLM provider"
            )

        # Initialize model client
        # For non-OpenAI models, we need to provide model_info
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

        self.agents = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agents with tools"""

        # Define all available tools
        tools = [
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
        ]

        # Coding Agent - Generates code (tools disabled for DeepSeek compatibility)
        simple_prompt = """You are an expert React/TypeScript developer.

When asked to create components or write code, you MUST:
1. Generate complete, working code
2. Wrap ALL code in markdown code blocks with language (```tsx, ```ts, ```css)
3. Use TypeScript with proper types
4. Use Tailwind CSS for styling
5. Make code production-ready

Example:
```tsx
import React from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
}

export const Button: React.FC<ButtonProps> = ({ label, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
    >
      {label}
    </button>
  );
};
```

Always generate complete code in markdown blocks."""

        self.coding_agent = AssistantAgent(
            name="CodingAgent",
            description="Expert coding agent that generates React/TypeScript code",
            system_message=simple_prompt,
            model_client=self.model_client,
            tools=[],  # Temporarily disable tools for DeepSeek
            reflect_on_tool_use=False,
        )

        # UI Designer Agent - Focuses on UI/UX
        self.ui_designer = AssistantAgent(
            name="UIDesigner",
            description="UI/UX designer specialized in modern web design",
            system_message=UI_DESIGNER_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client,
            tools=tools,
            reflect_on_tool_use=True,
        )

        # Code Reviewer Agent - Reviews and improves code
        self.code_reviewer = AssistantAgent(
            name="CodeReviewer",
            description="Expert code reviewer with deep knowledge of best practices",
            system_message=CODE_REVIEWER_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client,
            tools=[read_file, grep_search, file_search],  # Read-only tools
            reflect_on_tool_use=True,
        )

        # Architect Agent - Designs system architecture
        self.architect = AssistantAgent(
            name="Architect",
            description="Software architect expert in designing scalable applications",
            system_message=ARCHITECT_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client,
            tools=[read_file, list_dir, grep_search, file_search],  # Read-only tools
            reflect_on_tool_use=True,
        )

        self.agents = {
            "coding": self.coding_agent,
            "ui_designer": self.ui_designer,
            "code_reviewer": self.code_reviewer,
            "architect": self.architect,
        }

    async def generate_code(self, user_request: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate code based on user request using the CodingAgent

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

        # Use CodingAgent directly for faster response
        response = await self.coding_agent.on_messages(
            [TextMessage(content=full_message, source="user")],
            CancellationToken()
        )

        # Extract code from response
        generated_code = []
        messages = []

        if response.chat_message:
            content = response.chat_message.content
            generated_code = self._extract_code_from_message(content)
            messages.append(self._message_to_dict(response.chat_message))

        return {
            "code": generated_code,
            "messages": messages,
            "success": len(generated_code) > 0,
            "response_text": response.chat_message.content if response.chat_message else "",
        }

    async def quick_code_generation(self, user_request: str, agent_type: str = "coding") -> str:
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
        response = await agent.on_messages(
            [TextMessage(content=user_request, source="user")],
            CancellationToken()
        )

        # Extract code from response
        if response.chat_message:
            code_blocks = self._extract_code_from_message(response.chat_message.content)
            if code_blocks:
                return code_blocks[0]['content']

        return ""

    async def review_code(self, code: str, context: Optional[str] = None) -> Dict:
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

        response = await self.code_reviewer.on_messages(
            [TextMessage(content=message, source="user")],
            CancellationToken()
        )

        if response.chat_message:
            return {
                "feedback": response.chat_message.content,
                "success": True,
            }

        return {"feedback": "", "success": False}

    def _message_to_dict(self, message) -> Dict:
        """Convert AutoGen message to dict"""
        return {
            "source": getattr(message, "source", "unknown"),
            "content": getattr(message, "content", ""),
            "type": message.__class__.__name__,
        }

    def _extract_code_from_messages(self, messages: List) -> List[Dict]:
        """Extract code blocks from conversation messages"""

        code_blocks = []

        for msg in messages:
            content = getattr(msg, "content", "")
            if isinstance(content, str):
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
