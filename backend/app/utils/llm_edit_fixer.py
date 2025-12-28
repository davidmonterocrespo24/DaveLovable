import json

import httpx
from autogen_core.models import SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.config import get_settings
from src.utils.deepseek_fix import should_use_reasoning_client
from src.utils.deepseek_reasoning_client import DeepSeekReasoningClient

# --- Prompt Configuration ---
EDIT_SYS_PROMPT = """
You are an expert code-editing assistant specializing in debugging and correcting failed search-and-replace operations.

# Primary Goal
Your task is to analyze a failed edit attempt and provide a corrected `search` string that will match the text in the file precisely. The correction should be as minimal as possible, staying very close to the original, failed `search` string. Do NOT invent a completely new edit based on the instruction; your job is to fix the provided parameters.

It is important that you do no try to figure out if the instruction is correct. DO NOT GIVE ADVICE. Your only goal here is to do your best to perform the search and replace task! 

# Input Context
You will be given:
1. The high-level instruction for the original edit.
2. The exact `search` and `replace` strings that failed.
3. The error message that was produced.
4. The full content of the latest version of the source file.

# Rules for Correction
1.  **Minimal Correction:** Your new `search` string must be a close variation of the original. Focus on fixing issues like whitespace, indentation, line endings, or small contextual differences.
2.  **Explain the Fix:** Your `explanation` MUST state exactly why the original `search` failed and how your new `search` string resolves that specific failure. (e.g., "The original search failed due to incorrect indentation; the new search corrects the indentation to match the source file.").
3.  **Preserve the `replace` String:** Do NOT modify the `replace` string unless the instruction explicitly requires it and it was the source of the error. Do not escape any characters in `replace`. Your primary focus is fixing the `search` string.
4.  **No Changes Case:** CRUCIAL: if the change is already present in the file,  set `noChangesRequired` to True and explain why in the `explanation`. It is crucial that you only do this if the changes outline in `replace` are already in the file and suits the instruction.
5.  **Exactness:** The final `search` field must be the EXACT literal text from the file. Do not escape characters.
"""

EDIT_USER_PROMPT_TEMPLATE = """
# Goal of the Original Edit
<instruction>
{instruction}
</instruction>

# Failed Attempt Details
- **Original `search` parameter (failed):**
<search>
{old_string}
</search>
- **Original `replace` parameter:**
<replace>
{new_string}
</replace>
- **Error Encountered:**
<error>
{error}
</error>

# Full File Content
<file_content>
{current_content}
</file_content>

# Your Task
Based on the error and the file content, provide a corrected `search` string that will succeed. Remember to keep your correction minimal and explain the precise reason for the failure in your `explanation`.
Return valid JSON.
"""


# --- Implementation ---


async def _llm_fix_edit(
    instruction: str, old_string: str, new_string: str, error_msg: str, file_content: str
) -> tuple[str, str] | None:
    """
    Attempts to correct old_string and new_string using an LLM when search fails.
    Replicating the logic of Google's FixLLMEditWithInstruction.
    """

    user_prompt = EDIT_USER_PROMPT_TEMPLATE.format(
        instruction=instruction,
        old_string=old_string,
        new_string=new_string,
        error=error_msg,
        current_content=file_content,
    )

    settings = get_settings()

    # Create http client
    http_client = httpx.AsyncClient(verify=settings.ssl_verify)

    try:
        if should_use_reasoning_client(settings):
            client = DeepSeekReasoningClient(
                model=settings.model,
                base_url=settings.base_url,
                api_key=settings.api_key,
                model_capabilities=settings.get_model_capabilities(),
                http_client=http_client,
                enable_thinking=None,
                response_format={"type": "json_object"},
            )
        else:
            client = OpenAIChatCompletionClient(
                model=settings.model,
                base_url=settings.base_url,
                api_key=settings.api_key,
                model_capabilities=settings.get_model_capabilities(),
                http_client=http_client,
                response_format={"type": "json_object"},
            )

        messages = [
            SystemMessage(content=EDIT_SYS_PROMPT),
            UserMessage(content=user_prompt, source="user"),
        ]

        result = await client.create(messages)
        response_content = result.content
        if response_content.strip().startswith("```"):
            response_content = response_content.split("```json")[-1].split("```")[0].strip()

        data = json.loads(response_content)

        if data.get("noChangesRequired", False):
            # El LLM dice que ya está hecho.
            # Podríamos lanzar una excepción específica o retornar los valores originales
            # para que el validador de "no changes" lo capture arriba.
            return old_string, old_string  # Esto disparará 'new == old' error

        corrected_search = data.get("search", old_string)
        corrected_replace = data.get("replace", new_string)

        return corrected_search, corrected_replace

    except Exception as e:
        print(f"Error en _llm_fix_edit: {e}")
        return None
    finally:
        await http_client.aclose()
