#  Enterprise Policy Agent

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)
![React](https://img.shields.io/badge/React-18.2-61dafb)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)

An event-driven, production-ready AI application designed to ingest, process, and query enterprise policy documents.

By leveraging a **Retrieval-Augmented Generation (RAG)** pipeline, this system intelligently answers natural language questions based on department-specific knowledge bases and generates context-aware compliance policies.

---

##  Key Features

- ** Intelligent RAG Pipeline**
  - Semantic search using ChromaDB and SentenceTransformers.
  - Groq-powered LLM inference for fast responses.

- ** Asynchronous Processing**
  - Heavy PDF parsing and embedding are decoupled from the main API.
  - Uses Confluent Kafka in KRaft mode.

- ** Context-Aware Filtering**
  - Strict separation of documents and queries by department and category.
  - Ensures retrieved context is relevant to the requested scope.

- ** Fully Containerized**
  - One-command deployment using Docker Compose.
  - Persistent Docker volumes for databases, documents, and vector storage.

- ** Type-Safe & Scalable**
  - FastAPI with Pydantic validation.
  - React with Vite for the frontend.
  - SQLAlchemy for database operations.

---

##  Architecture Flow

The application follows an event-driven RAG architecture.

### 1. User Action

The user uploads a PDF through the React UI and assigns:

- Department
- Category

### 2. Synchronous API

FastAPI:

1. Receives the uploaded PDF.
2. Saves the file to the shared volume.
3. Stores document metadata in MySQL.
4. Publishes an `indexing_task` event to Kafka.

### 3. Asynchronous Worker

The Python worker:

1. Consumes the Kafka event.
2. Reads the PDF from the shared volume.
3. Extracts and chunks the document text.
4. Generates embeddings.
5. Stores the resulting vectors in ChromaDB.

### 4. Query Phase

When a user asks a question:

1. FastAPI receives the query.
2. Relevant documents are retrieved from ChromaDB.
3. Department/category filters are applied.
4. Relevant context is added to the prompt.
5. The prompt is sent to the Groq LLM API.
6. The generated answer is returned to the user.

---

##  Project Structure

```text
enterprise-policy-agent/
│
├── .env                         # Global environment variables
├── docker-compose.yml           # Orchestrates the container cluster
│
├── frontend/                    # React UI
│   ├── src/                     # Components, Pages, and API services
│   ├── package.json
│   ├── vite.config.js
│   └── .dockerignore            # Optimizes UI build context
│
└── backend/                     # Python API & Background Worker
    ├── app/
    │   ├── main.py              # FastAPI application entry point
    │   ├── worker.py            # Kafka consumer and ChromaDB indexer
    │   ├── models.py            # SQLAlchemy ORM models
    │   ├── database.py          # MySQL connection and session management
    │   └── routes/              # API endpoints
    │
    ├── requirements.txt         # Python dependencies
    ├── Dockerfile               # Shared image for API and Worker
    └── .dockerignore            # Prevents copying unnecessary files


 Getting Started
1. Prerequisites
Make sure the following are installed:

Docker

Docker Compose v2

A valid API key from Groq Console

2. Environment Configuration
Create a .env file in the root directory:

GROQ_API_KEY=your_actual_groq_api_key_here

MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=policy_db
MYSQL_USER=user
MYSQL_PASSWORD=password

3. Build & Deploy
Launch the complete application stack in detached mode:

docker-compose up -d --build

The initial build may take several minutes because the backend image needs to download Python dependencies, including PyTorch.

For subsequent launches:

docker-compose up -d

Check running containers:

docker-compose ps

View logs:

docker-compose logs -f

API Endpoints Reference
Once the application is running, the interactive Swagger UI is available at:

http://localhost:8000/docs

Documents
Method	Endpoint	Description
POST	/api/documents/upload	Upload a PDF, save metadata to SQL, and trigger Kafka indexing
GET	/api/documents/	Fetch indexed documents, optionally filtered by department

Policy & Querying
Method	Endpoint	Description
POST	/api/query	Ask a question against the RAG knowledge base
POST	/api/policies/generate	Generate a new policy document based on seed inputs

Data Persistence & Volumes
The application uses Docker volumes to ensure data persists between container restarts.

Volume	Purpose
mysql_data	Stores user profiles, document metadata, and SQL records
shared_docs	Stores raw PDF files shared between the API and Worker
chroma_data	Stores ChromaDB vector data

Persistent Storage
Persistent volumes prevent data loss when containers are restarted or recreated.

The following data is persisted:

Uploaded documents

Database records

Document metadata

Generated embeddings

ChromaDB indexes

Reset Everything
To stop the containers and remove all Docker volumes:

docker-compose down -v

Warning: This permanently removes the persisted MySQL, document, and ChromaDB data.

After resetting, rebuild and start the application:

docker-compose up -d --build

Troubleshooting
1. Port 3306 Conflict — MySQL
If Docker fails to start the database service because port 3306 is already in use, you may have a local MySQL instance running.

The Docker Compose configuration exposes MySQL externally on port 3307:

ports:
  - "3307:3306"

This means:

Host machine: 3307
       │
       ▼
Container:   3306

You can keep your local MySQL instance running while the Dockerized MySQL database uses port 3307.

2. Docker Build Taking Too Long
Make sure .dockerignore files exist in both the backend/ and frontend/ directories.

Backend .dockerignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.git/
.env

Frontend .dockerignore
node_modules/
dist/
.git/
.env

This prevents Docker from copying unnecessary files such as:

Python virtual environments

Python cache files

node_modules

Build output

Git metadata

3. Database Connection Refused
Inside Docker Compose, services should communicate using their service names, not localhost.

Incorrect
mysql+pymysql://user:password@localhost:3306/policy_db

Correct
mysql+pymysql://user:password@db:3306/policy_db

Here, db refers to the MySQL service defined in docker-compose.yml.

4. Check Backend Logs
If the API or worker is not behaving correctly, inspect the container logs:

docker-compose logs -f backend

If the worker is a separate service:

docker-compose logs -f worker

To inspect all services:

docker-compose logs -f

5. Verify Container Status
Run:

docker-compose ps

All required services should show a running or healthy state.

If a container has stopped, inspect its logs:

docker-compose logs <service-name>


Application Data Flow
                    ┌──────────────────┐
                    │    React UI      │
                    └────────┬─────────┘
                             │
                             │ HTTP
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    │       API        │
                    └────────┬─────────┘
                             │
               ┌─────────────┴─────────────┐
               │                           │
               ▼                           ▼
        ┌──────────────┐           ┌────────────────┐
        │    MySQL     │           │ Shared Volume  │
        │  Metadata    │           │   PDF Files    │
        └──────────────┘           └───────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │      Kafka      │
                                  │ indexing_task   │
                                  └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │     Worker      │
                                  │ PDF + Embedding │
                                  └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │    ChromaDB     │
                                  │  Vector Store   │
                                  └────────┬────────┘
                                           │
                                           │ Query
                                           ▼
                                  ┌─────────────────┐
                                  │   Groq LLM API  │
                                  └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │  Final Answer   │
                                  └─────────────────┘

Security Considerations
Before deploying this application to production, consider implementing the following:

Store secrets using a secure secrets manager.

Never commit .env files to Git.

Add authentication and authorization to API endpoints.

Validate uploaded PDF files and enforce size limits.

Restrict document access based on user permissions.

Apply rate limiting to public-facing APIs.

Configure CORS appropriately.

Use HTTPS in production.

Secure Kafka and MySQL credentials.

Keep Docker images and Python/Node dependencies updated.

Scalability
The architecture allows individual components to scale independently.

For example, additional workers can consume Kafka events as document-processing workloads increase:

             ┌─────────────┐
             │   FastAPI   │
             └──────┬──────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   ┌─────────────┐     ┌─────────────┐
   │   Worker 1  │     │   Worker 2  │
   └──────┬──────┘     └──────┬──────┘
          │                   │
          └─────────┬─────────┘
                    ▼
               ┌─────────┐
               │  Kafka  │
               └─────────┘

This allows document processing capacity to grow independently from the API layer.

Development
For local development, FastAPI provides an interactive Swagger interface:

http://localhost:8000/docs

An alternative ReDoc interface is available at:

http://localhost:8000/redoc
