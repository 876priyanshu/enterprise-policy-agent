
from app.routes.document import collection

def search_internal_docs(query: str, threshold: float = 0.15) -> str:
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    
    if not documents or not distances:
        return "NO_RESULTS: No internal policy documents found."

    # Assuming Cosine Similarity (Higher is better)
    best_score = max(distances)
    
    if best_score < threshold:
        # This exact string tells the LLM to pivot
        return "NO_RESULTS: The internal documents retrieved were not relevant enough to answer this query."

    # If it passes the threshold, format normally
    context = "\n\n".join(documents)
    return f"Internal Policy Context:\n{context}"