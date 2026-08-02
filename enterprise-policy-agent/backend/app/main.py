from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize the FastAPI application (Similar to `const app = express()`)
app = FastAPI(
    title="Enterprise Policy Agent API",
    description="Backend for querying enterprise policies using RAG and Grok",
    version="1.0.0"
)

# CORS Configuration (Similar to `app.use(cors())` in Express)
# This allows our React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be your frontend's specific URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allows all headers (including Authorization for JWT)
)

# A simple health-check route
@app.get("/")
def health_check():
    return {
        "status": "success",
        "message": "Enterprise Policy Agent API is running!"
    }