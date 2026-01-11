"""
Wikipedia Tools for AutoGen - Wikipedia search and content access
"""

import logging
from importlib import util


def _check_wikipedia():
    """Checks if wikipedia is installed"""
    if util.find_spec("wikipedia") is None:
        raise ImportError("wikipedia package not available. Install with: pip install wikipedia")
    import wikipedia

    wikipedia.set_lang("es")  # Set default language
    return wikipedia


async def wiki_search(query: str, max_results: int = 10) -> str:
    """
    Searches Wikipedia and returns related page titles.

    Args:
        query: Search query
        max_results: Maximum number of results (default: 10)

    Returns:
        str: List of found titles or error message
    """
    try:
        wikipedia = _check_wikipedia()
        search_results = wikipedia.search(query, results=max_results, suggestion=True)

        if isinstance(search_results, tuple):
            results, suggestion = search_results
            output = f"Search results for '{query}':\n\n"
            for i, title in enumerate(results, 1):
                output += f"{i}. {title}\n"
            if suggestion:
                output += f"\nDid you mean?: {suggestion}"
            return output
        else:
            output = f"Search results for '{query}':\n\n"
            for i, title in enumerate(search_results, 1):
                output += f"{i}. {title}\n"
            return output

    except Exception as e:
        error_msg = f"Error searching Wikipedia '{query}': {e!s}"
        logging.error(error_msg)
        return error_msg


async def wiki_summary(title: str, sentences: int = 5) -> str:
    """
    Gets a summary of a Wikipedia page.

    Args:
        title: Wikipedia page title
        sentences: Number of summary sentences (default: 5)

    Returns:
        str: Page summary or error message
    """
    try:
        wikipedia = _check_wikipedia()
        summary = wikipedia.summary(title, sentences=sentences, auto_suggest=True)
        return f"=== {title} ===\n\n{summary}"

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:10]  # Limit to 10 options
        output = f"'{title}' is a disambiguation page. Options:\n\n"
        for i, option in enumerate(options, 1):
            output += f"{i}. {option}\n"
        return output

    except wikipedia.exceptions.PageError:
        return f"ERROR: Page '{title}' not found on Wikipedia"

    except Exception as e:
        error_msg = f"Error getting summary of '{title}': {e!s}"
        logging.error(error_msg)
        return error_msg


async def wiki_content(title: str, max_chars: int = 5000) -> str:
    """
    Gets the full content of a Wikipedia page.

    Args:
        title: Wikipedia page title
        max_chars: Maximum characters to return (default: 5000)

    Returns:
        str: Page content or error message
    """
    try:
        wikipedia = _check_wikipedia()
        page = wikipedia.page(title, auto_suggest=True)

        content = f"=== {page.title} ===\n"
        content += f"URL: {page.url}\n\n"
        content += page.content

        # Limit characters if necessary
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... (content truncated)"

        return content

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:10]
        output = f"'{title}' is a disambiguation page. Options:\n\n"
        for i, option in enumerate(options, 1):
            output += f"{i}. {option}\n"
        return output

    except wikipedia.exceptions.PageError:
        return f"ERROR: Page '{title}' not found on Wikipedia"

    except Exception as e:
        error_msg = f"Error getting content of '{title}': {e!s}"
        logging.error(error_msg)
        return error_msg


async def wiki_page_info(title: str) -> str:
    """
    Gets detailed information about a Wikipedia page.

    Args:
        title: Wikipedia page title

    Returns:
        str: Detailed page information
    """
    try:
        wikipedia = _check_wikipedia()
        page = wikipedia.page(title, auto_suggest=True)

        output = f"=== Information for: {page.title} ===\n\n"
        output += f"URL: {page.url}\n"
        output += f"Summary: {page.summary[:300]}...\n\n"
        output += f"Categories ({len(page.categories)}):\n"
        for cat in page.categories[:10]:
            output += f"  - {cat}\n"

        output += f"\nRelated links ({len(page.links)}):\n"
        for link in page.links[:10]:
            output += f"  - {link}\n"

        output += f"\nReferences: {len(page.references)} links\n"
        output += f"Images: {len(page.images)} images\n"

        return output

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:10]
        output = f"'{title}' is a disambiguation page. Options:\n\n"
        for i, option in enumerate(options, 1):
            output += f"{i}. {option}\n"
        return output

    except wikipedia.exceptions.PageError:
        return f"ERROR: Page '{title}' not found on Wikipedia"

    except Exception as e:
        error_msg = f"Error getting information of '{title}': {e!s}"
        logging.error(error_msg)
        return error_msg


async def wiki_random(count: int = 1) -> str:
    """
    Gets titles of random Wikipedia pages.

    Args:
        count: Number of random pages (default: 1)

    Returns:
        str: Random page titles
    """
    try:
        wikipedia = _check_wikipedia()

        if count == 1:
            random_title = wikipedia.random()
            return f"Random page: {random_title}"
        else:
            random_titles = wikipedia.random(count)
            output = f"Random pages ({count}):\n\n"
            for i, title in enumerate(random_titles, 1):
                output += f"{i}. {title}\n"
            return output

    except Exception as e:
        error_msg = f"Error getting random pages: {e!s}"
        logging.error(error_msg)
        return error_msg


async def wiki_set_language(language: str) -> str:
    """
    Changes Wikipedia language.

    Args:
        language: Language code (e.g.: 'en', 'es', 'fr')

    Returns:
        str: Confirmation or error message
    """
    try:
        wikipedia = _check_wikipedia()
        wikipedia.set_lang(language)
        return f"✓ Wikipedia language changed to: {language}"

    except Exception as e:
        error_msg = f"Error changing language to '{language}': {e!s}"
        logging.error(error_msg)
        return error_msg
