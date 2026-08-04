agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_policy_docs",
            "description": "Use this FIRST to search internal company policies, guidelines, and proprietary documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query for internal documents."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Use this ONLY when the question is not covered by internal policy documents, or when it asks about external, public, or current events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query for the public web."}
                },
                "required": ["query"],
            },
        },
    }
]