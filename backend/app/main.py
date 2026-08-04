# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.database import engine, Base
# 1. ADD 'query' TO YOUR IMPORTS HERE
from app.routes import auth, policy, document, query 
from app.limiter import limiter

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)

# 2. ADD THE QUERY ROUTER HERE (Make sure it is ABOVE policy.router)
app.include_router(query.router, prefix="/api/policy", tags=["Agent"])

app.include_router(policy.router, prefix="/api/policy", tags=["Policy"])
app.include_router(document.router, prefix="/documents", tags=["documents"])

@app.get("/")
def health_check():
    return {"status": "success", "message": "Enterprise Policy Agent API is running!"}