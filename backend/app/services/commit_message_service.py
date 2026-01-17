import json

import httpx
import tiktoken
from autogen_core.models import SystemMessage, UserMessage

from app.core.config import settings
from app.core.gemini_client import Gemini3FlashChatCompletionClient


class CommitMessageService:
    """Service for generating Git commit messages using LLM"""

    @staticmethod
    def count_tokens(text: str) -> int:
        """
        Count the number of tokens in a text string

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate of 1 token per 4 characters
            return len(text) // 4

    @staticmethod
    def truncate_diff(diff: str, max_tokens: int = 900000) -> str:
        """
        Truncate diff to stay under token limit

        Args:
            diff: The git diff output
            max_tokens: Maximum allowed tokens (default: 900k for input, leaving 100k buffer and 64k for output)
                       Gemini-3 Flash supports 1M input tokens and 64K output tokens

        Returns:
            Truncated diff
        """
        token_count = CommitMessageService.count_tokens(diff)

        if token_count <= max_tokens:
            return diff

        # If too long, truncate by taking first part and last part
        # This gives context about both what was added and the overall scope
        lines = diff.split("\n")
        total_lines = len(lines)

        # Take 70% from start, 30% from end
        start_lines = int(total_lines * 0.7)
        end_lines = int(total_lines * 0.3)

        truncated = "\n".join(lines[:start_lines])
        truncated += f"\n\n... [Diff truncated: {total_lines - start_lines - end_lines} lines omitted] ...\n\n"
        truncated += "\n".join(lines[-end_lines:])

        # Double check it's under limit
        if CommitMessageService.count_tokens(truncated) > max_tokens:
            # If still too long, be more aggressive
            start_lines = int(total_lines * 0.5)
            end_lines = int(total_lines * 0.2)
            truncated = "\n".join(lines[:start_lines])
            truncated += f"\n\n... [Diff truncated: {total_lines - start_lines - end_lines} lines omitted] ...\n\n"
            truncated += "\n".join(lines[-end_lines:])

        return truncated

    @staticmethod
    async def generate_commit_message(diff: str, user_request: str = "") -> dict:
        """
        Generate a Git commit message based on the diff and user request

        Args:
            diff: The git diff output showing changes
            user_request: The original user request that led to these changes

        Returns:
            Dictionary with 'title' (short message) and 'body' (detailed description)
        """
        # Truncate diff to stay under token limit (Gemini-3 Flash: 1M input tokens)
        truncated_diff = CommitMessageService.truncate_diff(diff, max_tokens=900000)

        # Build system and user messages
        system_prompt = "You are a helpful assistant that generates concise, meaningful Git commit messages. Always respond in valid JSON format."

        user_prompt = f"""You are a Git commit message generator. Analyze the following git diff and create a concise, meaningful commit message.

User Request: {user_request if user_request else "AI-generated changes"}

Git Diff:
{truncated_diff}

Create a commit message following conventional commits format:
- Title: One line (max 72 chars) summarizing the changes (e.g., "feat: add user authentication", "fix: resolve login bug")
- Body: 2-4 sentences explaining what was changed and why

Respond in JSON format:
{{
  "title": "feat: your commit title here",
  "body": "Detailed description of changes made..."
}}"""

        # Create http client
        http_client = httpx.AsyncClient()

        try:
            # Create Gemini-3 Flash client
            client = Gemini3FlashChatCompletionClient(
                temperature=0.3, max_tokens=500, http_client=http_client, response_format={"type": "json_object"}
            )

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt, source="user"),
            ]

            # Call the model
            result = await client.create(messages)
            response_content = result.content

            # Handle potential code block wrapping
            if response_content.strip().startswith("```"):
                response_content = response_content.split("```json")[-1].split("```")[0].strip()

            # Parse JSON response
            data = json.loads(response_content)

            return {
                "title": data.get("title", "chore: AI-generated changes"),
                "body": data.get("body", "Automated commit from AI agent system"),
            }

        except Exception as e:
            print(f"Error generating commit message: {e}")
            # Fallback message
            return {
                "title": "chore: AI-generated changes",
                "body": f"Automated commit from AI agent system\n\nUser request: {user_request if user_request else 'N/A'}",
            }
        finally:
            await http_client.aclose()
