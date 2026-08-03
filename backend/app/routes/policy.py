import httpx

from pydantic import BaseModel
from app.core.config import settings
from app.services.security import get_current_user
from app.models.user import User
from sqlalchemy.orm import Session
from app.core.database import get_db  # Adjust if your dependency is located elsewhere
from app.models.policy import Policy
from datetime import datetime
from typing import List
from typing import Optional
from typing import Literal
from fastapi import Query
from sqlalchemy import asc, desc
from fastapi import HTTPException, status
from fastapi import Request
from app.limiter import limiter
import openai  # Groq SDK uses standard OpenAI client exceptions under the hood
from fastapi import APIRouter, Depends, HTTPException, status
import os

# 1. Initialize the Groq client using the OpenAI SDK
groq_client = openai.OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

router = APIRouter()


class PolicyGenerateRequest(BaseModel):
    title: str
    prompt: str


class PolicyRequest(BaseModel):
    title: str
    prompt: str

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class PolicyResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    # This tells Pydantic to read standard object attributes (not just dictionaries)
    model_config = {"from_attributes": True}
@router.post("/generate")
async def generate_policy(request: PolicyRequest, current_user: User = Depends(get_current_user)):
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-oss-120b",  # The current recommended open model on Groq
        "messages": [
            {"role": "system", "content": "You are an Enterprise Security Policy AI. Output strictly professional, formatted policy text."},
            {"role": "user", "content": request.prompt}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Pointing to GroqCloud's OpenAI-compatible endpoint
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45.0 
            )
            
            response.raise_for_status() 
            
            data = response.json()
            policy_text = data["choices"][0]["message"]["content"]
            
            return {"status": "success", "policy": policy_text}
            
        except httpx.HTTPStatusError as e:
            print(f"Groq API Error: {e.response.text}") 
            raise HTTPException(
                status_code=e.response.status_code, 
                detail="Failed to generate policy from AI provider."
            )

@router.post("/generate")
async def generate_policy(
    request: PolicyRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)  # <-- Inject the database session
):
    # ... [Keep your existing Groq API setup and httpx call exactly as is] ...
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(...)
            response.raise_for_status() 
            
            data = response.json()
            policy_text = data["choices"][0]["message"]["content"]
            
            # --- NEW DATABASE LOGIC ---
            
            # 1. Instantiate the Python object 
            new_policy = Policy(
                title=request.title,
                content=policy_text,
                user_id=current_user.id
            )
            
            # 2. Stage the object in the current transaction
            db.add(new_policy)
            
            # 3. Flush the transaction to MySQL
            db.commit()
            
            # 4. Refresh the object to get the auto-generated ID and timestamps
            db.refresh(new_policy)
            
            return {
                "status": "success", 
                "policy_id": new_policy.id,
                "title": new_policy.title,
                "policy": new_policy.content
            }
            
        except httpx.HTTPStatusError as e:
            print(f"Groq API Error: {e.response.text}") 
            raise HTTPException(
                status_code=e.response.status_code, 
                detail="Failed to generate policy from AI provider."
            )

@router.get("/", response_model=list[PolicyResponse])
async def get_user_policies(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Max items per page"),
    sort_by: Literal["created_at", "title"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Dynamically select sort column and direction
    sort_column = getattr(Policy, sort_by)
    direction = desc(sort_column) if order == "desc" else asc(sort_column)

    policies = (
        db.query(Policy)
        .filter(Policy.user_id == current_user.id)
        .order_by(direction)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return policies


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(
        Policy.id == policy_id, 
        Policy.user_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
        
    return policy

@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: int,
    policy_update: PolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(
        Policy.id == policy_id, 
        Policy.user_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    
    # Mutate the fields only if the user provided new data
    if policy_update.title is not None:
        policy.title = policy_update.title
    if policy_update.content is not None:
        policy.content = policy_update.content
        
    db.commit()
    db.refresh(policy) # Refresh re-syncs the Python object with the new database state
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(
        Policy.id == policy_id, 
        Policy.user_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    
    db.delete(policy)
    db.commit()
    return None


@router.post("/generate", response_model=PolicyResponse)
@limiter.limit("5/minute")  # Returns 429 Too Many Requests if exceeded
async def generate_policy(
    request: Request, # Required by slowapi
    policy_req: PolicyGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are an enterprise policy writer."},
                {"role": "user", "content": request.prompt}
            ],
            timeout=15.0  # Prevents thread hanging forever
        )
        policy_content = response.choices[0].message.content

    except openai.APITimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI generation timed out. Please try again."
        )
    except openai.APIError as e:
        # Catches 5xx/4xx errors from Groq/upstream without crashing our app
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI Service currently unavailable: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during generation."
        )

    # Save to database...
    new_policy = Policy(
        title=request.title,
        content=policy_content,
        user_id=current_user.id
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return new_policy