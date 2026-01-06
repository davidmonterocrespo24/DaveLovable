import tiktoken
import httpx
import json
from autogen_core.models import SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from app.core.config import settings


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
    def truncate_diff(diff: str, max_tokens: int = 100000) -> str:
        """
        Truncate diff to stay under token limit

        Args:
            diff: The git diff output
            max_tokens: Maximum allowed tokens (default: 100k, leaving 20k for prompt/response)

        Returns:
            Truncated diff
        """
        token_count = CommitMessageService.count_tokens(diff)

        if token_count <= max_tokens:
            return diff

        # If too long, truncate by taking first part and last part
        # This gives context about both what was added and the overall scope
        lines = diff.split('\n')
        total_lines = len(lines)

        # Take 70% from start, 30% from end
        start_lines = int(total_lines * 0.7)
        end_lines = int(total_lines * 0.3)

        truncated = '\n'.join(lines[:start_lines])
        truncated += f"\n\n... [Diff truncated: {total_lines - start_lines - end_lines} lines omitted] ...\n\n"
        truncated += '\n'.join(lines[-end_lines:])

        # Double check it's under limit
        if CommitMessageService.count_tokens(truncated) > max_tokens:
            # If still too long, be more aggressive
            start_lines = int(total_lines * 0.5)
            end_lines = int(total_lines * 0.2)
            truncated = '\n'.join(lines[:start_lines])
            truncated += f"\n\n... [Diff truncated: {total_lines - start_lines - end_lines} lines omitted] ...\n\n"
            truncated += '\n'.join(lines[-end_lines:])

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
        # Truncate diff to stay under token limit
        truncated_diff = CommitMessageService.truncate_diff(diff, max_tokens=100000)

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
            # Get model capabilities
            model_info = {
                "vision": True,
                "function_calling": True,
                "json_output": True,
                "family": "unknown",
                "structured_output": True,
            }

            # Create OpenAI client using AutoGen
            client = OpenAIChatCompletionClient(
                model=settings.OPENAI_MODEL,
                base_url=settings.OPENAI_API_BASE_URL if settings.OPENAI_API_BASE_URL else None,
                api_key=settings.OPENAI_API_KEY,
                model_capabilities=model_info,
                http_client=http_client,
            )

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt, source="user"),
            ]

            # Call the model with extra parameters for OpenAI
            result = await client.create(
                messages,
                extra_create_args={
                    "temperature": 0.3,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"}
                }
            )
            response_content = result.content

            # Handle potential code block wrapping
            if response_content.strip().startswith("```"):
                response_content = response_content.split("```json")[-1].split("```")[0].strip()

            # Parse JSON response
            data = json.loads(response_content)

            return {
                "title": data.get("title", "chore: AI-generated changes"),
                "body": data.get("body", "Automated commit from AI agent system")
            }

        except Exception as e:
            print(f"Error generating commit message: {e}")
            # Fallback message
            return {
                "title": "chore: AI-generated changes",
                "body": f"Automated commit from AI agent system\n\nUser request: {user_request if user_request else 'N/A'}"
            }
        finally:
            await http_client.aclose()
