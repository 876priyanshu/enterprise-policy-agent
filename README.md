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
