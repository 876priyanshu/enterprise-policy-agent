import logging
import json
import time
from fastapi import APIRouter, Request, Depends
from app.services.tools import agent_tools
from app.services.web_search import perform_web_search
from app.services.rag import search_internal_docs
from app.routes.document import QueryRequest, groq_client
from app.services.security import get_current_user  # Corrected import
from loguru import logger # <-- Swap standard logging for loguru
from openai import APIError, APITimeoutError # <-- Import OpenAI exceptions for Groq
from fastapi import HTTPException
from prometheus_client import Counter
from app.services.tools import agent_tools

router = APIRouter()

LLM_TOKEN_COUNTER = Counter(
    "agent_llm_tokens_total",
    "Total tokens consumed by the Groq LLM",
    ["token_type"] # Label to split by prompt vs. completion
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a strict, enterprise-grade policy assistant. You have access to two tools:
1. `search_policy_docs` for internal company policies.
2. `web_search` for public/external information.

RULES:
- ALWAYS try `search_policy_docs` first if the user is asking about company rules, HR, or internal systems.
- If `search_policy_docs` returns "NO_RESULTS", you MUST fall back to `web_search`.
- You MUST explicitly state your source in your final answer (e.g., "According to internal policies..." or "Based on a web search...").
- If neither tool returns relevant information, say: "I don't have information on that." DO NOT guess or hallucinate.
"""

@router.post("/query")
async def query_agent(
    request: Request, 
    payload: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": payload.question})
    
    source_used = "none"
    max_iterations = 3
    current_iteration = 0
    answer = ""
    
    # Contextualize all logs in this function with the user's ID
    with logger.contextualize(user_id=current_user.id):
        logger.info(f"Starting agent execution for question: '{payload.question}'")

        while current_iteration < max_iterations:
            llm_start_time = time.time()
            try:
                # 1. Call the LLM
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    tools=agent_tools,
                    tool_choice="auto"
                )
                if response.usage:
                    logger.info(
                            f"Iteration {current_iteration} Tokens | "
                            f"Prompt: {response.usage.prompt_tokens} | "
                            f"Completion: {response.usage.completion_tokens} | "
                            f"Total: {response.usage.total_tokens}"
                        )
                    
                LLM_TOKEN_COUNTER.labels(token_type="prompt").inc(response.usage.prompt_tokens)
                LLM_TOKEN_COUNTER.labels(token_type="completion").inc(response.usage.completion_tokens)
    

                llm_latency = time.time() - llm_start_time
                logger.debug(f"Groq LLM call succeeded in {llm_latency:.4f}s (Iteration {current_iteration})")

            except APITimeoutError as e:
                logger.error(f"Groq API timed out after {time.time() - llm_start_time:.4f}s")
                raise HTTPException(status_code=504, detail="AI generation timed out.")
            except APIError as e:
                logger.exception(f"Groq API Error: {e.message}")
                raise HTTPException(status_code=502, detail="Upstream AI provider error.")

            message = response.choices[0].message
            
            # ... [Keep your existing tool routing logic exactly the same] ...
            
        # ... [Keep your existing fallback logic] ...

        logger.info(
            f"Agent finished | Source: {source_used} | "
            f"Iterations: {current_iteration}"
        )

        return {"answer": answer, "source": source_used}