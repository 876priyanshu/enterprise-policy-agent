import logging
import json
from fastapi import APIRouter, Request, Depends
from app.services.tools import agent_tools
from app.services.web_search import perform_web_search
from app.services.rag import search_internal_docs
from app.routes.document import QueryRequest, groq_client
from app.services.security import get_current_user  # Corrected import

router = APIRouter()
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
    max_iterations = 3  # Safety breaker to prevent infinite loops
    current_iteration = 0
    answer = ""
    
    while current_iteration < max_iterations:
        # 1. Call the LLM
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=agent_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # 2. Check if the LLM is done searching
        if not message.tool_calls:
            # No tools called? The LLM has formulated its final answer.
            answer = message.content
            break
            
        # 3. If tools were called, execute them
        messages.append(message) # Append the LLM's tool call intent to history
        
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            tool_result = ""
            
            # ROUTE: Internal Search
            if function_name == "search_policy_docs":
                tool_result = search_internal_docs(args.get("query"))
                if "NO_RESULTS" not in tool_result:
                    source_used = "internal_docs"
            
            # ROUTE: Web Search
            elif function_name == "web_search":
                tool_result = await perform_web_search(args.get("query"))
                source_used = "web_search"
                
            # Append the tool's actual output back into the message history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": tool_result
            })
            
        current_iteration += 1

    # 4. Fallback if the loop maxes out
    if current_iteration >= max_iterations and not answer:
        answer = "I'm sorry, I couldn't find a conclusive answer after multiple searches."

    # 5. Log and return
    logger.info(
        f"Query processed | User: {current_user.id} | "
        f"Source: {source_used} | Iterations: {current_iteration}"
    )

    return {"answer": answer, "source": source_used}