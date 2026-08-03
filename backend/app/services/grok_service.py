import os
import httpx
from fastapi import HTTPException

GROK_API_URL = "https://api.x.ai/v1/chat/completions"

async def ask_grok_about_policy(user_query: str) -> str:
    """
    Sends a query to the Grok API and returns the AI's response.
    """
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Grok API key not configured.")

    # Clean the key of any accidental whitespace or quotes
    clean_api_key = api_key.strip().strip("\"'")

    headers = {
        "Authorization": f"Bearer {clean_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-4.5", # Or whichever specific Grok model you are targeting
        "messages": [
            {"role": "system", "content": "You are an expert Enterprise Policy Agent. Provide clear, professional advice based on standard corporate policies."},
            {"role": "user", "content": user_query}
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GROK_API_URL, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status() # Throws an error for 4xx/5xx responses
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Grok API Error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to communicate with AI: {str(e)}")