"""
Web Search Tool - Real-time web search using DuckDuckGo
"""

import logging
import random
import time
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


async def web_search(search_term: str, explanation: str = "", max_results: int = 5) -> str:
    """
    Search the web using web scraping from multiple search engines.

    Parameters:
        search_term (str): The search query to look for on the web
        explanation (str): Optional explanation for the web search operation
        max_results (int): Maximum number of search results to return (default: 5)

    Returns:
        str: Formatted search results with titles, URLs, and descriptions from multiple search engines
    """
    try:
        results = []

        # User agents to rotate for avoiding detection
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]

        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        # Try DuckDuckGo first (more scraping-friendly)
        try:
            results.extend(_search_duckduckgo(search_term, headers, max_results // 2))
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")

        # Try Bing as backup
        try:
            results.extend(_search_bing(search_term, headers, max_results // 2))
        except Exception as e:
            print(f"Bing search failed: {e}")

        # If no results, try a simple Google search (be cautious with rate limiting)
        if not results:
            try:
                results.extend(_search_google_simple(search_term, headers, max_results))
            except Exception as e:
                print(f"Google search failed: {e}")

        if not results:
            return f"No search results found for '{search_term}'. Search engines may be blocking requests."

        # Format results
        formatted_results = f"Web search results for: '{search_term}'\n"
        formatted_results += f"Found {len(results)} results:\n\n"

        for i, result in enumerate(results[:max_results], 1):
            formatted_results += f"{i}. **{result['title']}**\n"
            formatted_results += f"   URL: {result['url']}\n"
            formatted_results += (
                f"   Snippet: {result['snippet'][:200]}{'...' if len(result['snippet']) > 200 else ''}\n\n"
            )

        return formatted_results

    except Exception as e:
        return f"Error in web search: {e!s}"


def _search_duckduckgo(query: str, headers: dict, max_results: int) -> list[dict]:
    """Search DuckDuckGo"""
    results = []

    # DuckDuckGo HTML search
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Find search results
    result_divs = soup.find_all("div", class_="result")

    for div in result_divs[:max_results]:
        try:
            title_elem = div.find("a", class_="result__a")
            snippet_elem = div.find("a", class_="result__snippet")

            if title_elem and snippet_elem:
                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")
                snippet = snippet_elem.get_text(strip=True)

                if title and url:
                    results.append({"title": title, "url": url, "snippet": snippet or "No snippet available"})
        except Exception:
            continue

    return results


def _search_bing(query: str, headers: dict, max_results: int) -> list[dict]:
    """Search Bing"""
    results = []

    url = f"https://www.bing.com/search?q={quote_plus(query)}"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Find search results
    result_divs = soup.find_all("li", class_="b_algo")

    for div in result_divs[:max_results]:
        try:
            title_elem = div.find("h2")
            if title_elem:
                link_elem = title_elem.find("a")
                if link_elem:
                    title = link_elem.get_text(strip=True)
                    url = link_elem.get("href", "")

                    snippet_elem = div.find("p") or div.find("div", class_="b_caption")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No snippet available"

                    if title and url:
                        results.append({"title": title, "url": url, "snippet": snippet})
        except Exception:
            continue

    return results


def _search_google_simple(query: str, headers: dict, max_results: int) -> list[dict]:
    """Simple Google search (use sparingly to avoid rate limiting)"""
    results = []

    url = f"https://www.google.com/search?q={quote_plus(query)}"

    # Add delay to be respectful
    time.sleep(random.uniform(1, 3))

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Find search results (Google's structure changes frequently)
    result_divs = soup.find_all("div", class_="g")

    for div in result_divs[:max_results]:
        try:
            title_elem = div.find("h3")
            link_elem = div.find("a")

            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                url = link_elem.get("href", "")

                # Try to find snippet
                snippet_elem = div.find("span", {"data-content-id": True}) or div.find("div", class_="VwiC3b")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No snippet available"

                if title and url and not url.startswith("/search"):
                    results.append({"title": title, "url": url, "snippet": snippet})
        except Exception:
            continue

    return results


async def web_search_news(query: str, max_results: int = 5) -> str:
    """
    Search for recent news on the web.

    Args:
        query: News search query
        max_results: Maximum number of results (default: 5)

    Returns:
        str: Formatted news results
    """
    try:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "ERROR: duckduckgo_search is not installed.\nInstall with: pip install duckduckgo-search"

        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=max_results))
        except Exception as search_error:
            logging.error(f"Error in news search: {search_error}")
            return f"ERROR searching for news '{query}': {search_error!s}"

        if not results:
            return f"No news found for '{query}'"

        # Format results
        output = f"📰 News about: '{query}'\n"
        output += f"{'=' * 70}\n\n"

        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            snippet = result.get("body", "No description")
            url = result.get("url", "")
            date = result.get("date", "Unknown date")
            source = result.get("source", "Unknown source")

            output += f"{i}. **{title}**\n"
            output += f"   {snippet}\n"
            output += f"   📅 {date} | 📰 {source}\n"
            output += f"   🔗 {url}\n\n"

        return output

    except Exception as e:
        error_msg = f"Error en web_search_news: {e!s}"
        logging.error(error_msg)
        return error_msg
