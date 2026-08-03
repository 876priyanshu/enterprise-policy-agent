# backend/app/core/security.py
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt

# 1. Password Hashing Setup (Equivalent to bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_if_env_fails")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Equivalent to jwt.sign(payload, secret, { expiresIn })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt