# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# 1. Schema for reading data from the frontend (e.g., Registration)
class UserCreate(BaseModel):
    email: EmailStr  # Automatically validates that it's a proper email format
    password: str
    role: Optional[str] = "employee"

# 2. Schema for sending data back to the frontend (Hides password!)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Tells Pydantic to read data from SQLAlchemy ORM models