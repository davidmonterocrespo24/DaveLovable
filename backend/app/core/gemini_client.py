"""
Gemini-3 Flash Client
Centralized client configuration for Gemini-3 Flash API using OpenAI-compatible interface
"""

from typing import Optional

import httpx
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient

from app.core.config import settings


class Gemini3FlashChatCompletionClient(OpenAIChatCompletionClient):
    """
    Gemini-3 Flash client that extends OpenAIChatCompletionClient with
    pre-configured settings for Gemini API.

    This class centralizes the configuration of model capabilities and
    API settings, avoiding repetition across the codebase.

    Usage:
        # Simple usage with default settings
        client = Gemini3FlashChatCompletionClient()

        # With custom HTTP client
        http_client = httpx.AsyncClient()
        client = Gemini3FlashChatCompletionClient(http_client=http_client)

        # With custom parameters
        client = Gemini3FlashChatCompletionClient(
            temperature=0.5,
            max_tokens=4000
        )
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 64000,
        parallel_tool_calls: bool = False,
        http_client: Optional[httpx.AsyncClient] = None,
        response_format: Optional[dict] = None,
        **kwargs,
    ):
        """
        Initialize Gemini-3 Flash client with pre-configured settings.

        Gemini-3 Flash Preview Token Limits:
        - Input tokens: 1,000,000
        - Output tokens: 64,000
        - Total context window: ~1,064,000

        Args:
            model: Model name (defaults to settings.GEMINI_MODEL)
            api_key: API key (defaults to settings.GEMINI_API_KEY)
            base_url: Base URL (defaults to settings.GEMINI_API_BASE_URL)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens in response (default: 64000 - Gemini-3 Flash max output)
            parallel_tool_calls: Enable parallel tool calls (default: False)
            http_client: Optional HTTP client for requests
            response_format: Optional response format configuration
            **kwargs: Additional arguments passed to parent class
        """
        # Define model capabilities for Gemini-3 Flash
        model_info = ModelInfo(
            vision=True,
            function_calling=True,
            json_output=True,
            family="unknown",
            structured_output=True,
        )

        # Use settings if not provided
        model = model or settings.GEMINI_MODEL
        api_key = api_key or settings.GEMINI_API_KEY
        base_url = base_url or settings.GEMINI_API_BASE_URL

        # Initialize parent class with Gemini configuration
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            parallel_tool_calls=parallel_tool_calls,
            model_info=model_info,
            http_client=http_client,
            response_format=response_format,
            **kwargs,
        )


def create_gemini_client(
    temperature: float = 0.7,
    max_tokens: int = 64000,
    http_client: Optional[httpx.AsyncClient] = None,
    response_format: Optional[dict] = None,
) -> Gemini3FlashChatCompletionClient:
    """
    Factory function to create a Gemini-3 Flash client with common settings.

    This is a convenience function for creating clients with standard configuration.

    Args:
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens in response (default: 64000 - Gemini-3 Flash max)
        http_client: Optional HTTP client for requests
        response_format: Optional response format configuration

    Returns:
        Configured Gemini3FlashChatCompletionClient instance

    Example:
        client = create_gemini_client(temperature=0.3, max_tokens=500)
    """
    return Gemini3FlashChatCompletionClient(
        temperature=temperature,
        max_tokens=max_tokens,
        http_client=http_client,
        response_format=response_format,
    )
