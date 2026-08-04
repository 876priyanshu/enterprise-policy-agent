import uuid
import PyPDF2
from fastapi import APIRouter, UploadFile, File, HTTPException, status
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import os
from app.services.security import get_current_user
from pydantic import BaseModel
from openai import OpenAI
from typing import List, Optional
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends
# Assuming you have a dependency that yields a DB session:
from app.core.database import get_db 
from app.crud.chat import get_or_create_conversation, add_message, get_conversation_history
from app.limiter import limiter
from fastapi import Request, Depends

# Initialize Groq via the OpenAI SDK
groq_client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)



class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class QueryRequest(BaseModel):
    question: str
    n_results: int = 3
    conversation_id: Optional[str] = None




# 1. Initialize Vector Database (Saved locally to ./chroma_db)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# 2. Setup the local embedding model (Downloads automatically on first run)
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# 3. Create or load the collection
collection = chroma_client.get_or_create_collection(
    name="enterprise_policies",
    embedding_function=embedding_fn
)

router = APIRouter()



@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Only PDF files are supported."
        )
    
    try:
        # Extract text
        reader = PyPDF2.PdfReader(file.file)
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
            
        # Chunk text
        chunks = chunk_text(extracted_text, chunk_size=1000, overlap=200)
        
        if not chunks:
            raise ValueError("No readable text found in PDF.")
            
        # Prepare vector DB inputs
        # We use a UUID to ensure unique IDs across multiple uploads of the same file
        doc_id = str(uuid.uuid4())[:8]
        ids = [f"{file.filename}-{doc_id}-chunk-{i}" for i in range(len(chunks))]
        metadatas = [{"filename": file.filename, "chunk_index": i} for i in range(len(chunks))]
        
        # Store in ChromaDB (Embeddings are generated automatically here)
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "filename": file.filename, 
            "status": "success",
            "chunks_stored": len(chunks)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to process document: {str(e)}"
        )

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Splits text into overlapping chunks for better retrieval context."""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
        
    return chunks


@router.post("/query")
@limiter.limit("5/minute")
async def query_documents(
    request: Request,
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # <-- 1. Require Auth
):
    # 1. Manage Conversation State
    conv_id = get_or_create_conversation(
        db=db, 
        conversation_id=payload.conversation_id, 
        user_id=current_user.id  # <-- Bind state to the user
    )
    
    # 2. Save the incoming user question immediately
    add_message(db, conv_id, role="user", content=payload.question)
    
    # 3. Retrieve context from ChromaDB
    results = collection.query(
        query_texts=[payload.question],
        n_results=payload.n_results
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    
    context_str = "\n\n".join(
        f"[Source: {meta['filename']} | Chunk: {meta['chunk_index']}]\n{doc}" 
        for doc, meta in zip(documents, metadatas)
    ) if documents else "No relevant policies found."
    
    system_prompt = (
        "You are a strict, enterprise-grade policy assistant. "
        "Answer the user's question ONLY using the provided context. "
        "If the answer cannot be determined from the context, explicitly state: "
        "'I cannot answer this based on the provided policies.' Do not guess or hallucinate.\n\n"
        f"CONTEXT:\n{context_str}"
    )
    
    # 4. Fetch historical messages from MySQL and build the array
    db_history = get_conversation_history(db, conv_id)
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # The history from DB already includes the current user question (saved in step 2)
    for msg in db_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # 5. Generate Response via Groq
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant", 
            temperature=0.1, 
        )
        
        answer = chat_completion.choices[0].message.content
        
        # 6. Save the LLM's response back to MySQL
        add_message(db, conv_id, role="assistant", content=answer)
        
        return {
            "conversation_id": conv_id,
            "question": payload.question,
            "answer": answer,
            "sources": metadatas
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM Generation failed: {str(e)}"
        )

