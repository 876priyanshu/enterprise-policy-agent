import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

# In production, these should be loaded from your .env file
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-development-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# This tells FastAPI where the client can get a token (used for Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict):
    """Generates a new JWT token."""
    to_encode = data.copy()
    
    # Modern Python uses timezone-aware UTC dates
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Encode the payload into a secure JWT string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency that extracts the JWT token, verifies it, 
    and returns the active User database record.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except jwt.PyJWTError:
        # Catches expired tokens, invalid signatures, etc.
        raise credentials_exception
        
    # 2. Fetch the user from the database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    # 3. Check if the user is still active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user