import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def perform_web_search(query: str) -> str:
    """Calls the Tavily API to get a concise answer for the LLM."""
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": settings.TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "include_answer": True, # Asks Tavily to generate a short summary
        "max_results": 3        # Keep it small to save Groq token context
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Return Tavily's AI-generated answer plus the raw snippet context
            answer = data.get("answer", "")
            snippets = "\n".join([f"- {res['content']}" for res in data.get("results", [])])
            
            if not answer and not snippets:
                return "No relevant web search results found."
                
            return f"Web Search Summary: {answer}\n\nAdditional Context:\n{snippets}"
            
    except Exception as e:
        logger.error(f"Tavily search failed: {str(e)}")
        return "Web search is currently unavailable."
    