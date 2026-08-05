import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.database import engine, Base
from app.core.logger import setup_logging
from app.routes import auth, policy, document, query
from app.limiter import limiter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



Base.metadata.create_all(bind=engine)



app = FastAPI()

# Allow your local Vite development server
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"], # Allows all headers
)

# ... your existing endpoints ...






# This automatically tracks HTTP request metrics and exposes /metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Bind request-specific context (like IP) to the logger
    client_ip = request.client.host if request.client else "Unknown"
    req_id = request.headers.get("X-Request-ID", "N/A")
    
    with logger.contextualize(request_id=req_id, ip=client_ip):
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(f"{request.method} {request.url.path} completed in {process_time:.4f}s with status {response.status_code}")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"{request.method} {request.url.path} FAILED in {process_time:.4f}s | Error: {str(e)}")
            raise

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