# RAGForge AI

Intelligent Document Question & Answer System with Retrieval-Augmented Generation (RAG)

A full-stack AI application that enables users to upload PDF documents and ask intelligent questions about them, with AI-powered responses and automatic source citations.

## Overview

RAGForge AI solves the problem of quickly extracting information from multiple documents. Instead of manually reading through PDFs, users can upload documents and ask natural language questions. The system retrieves relevant content and generates accurate answers using an LLM, all while citing the source documents.

Main User Flow:
1. Upload PDF documents
2. System automatically chunks and embeds documents
3. Store embeddings in vector database
4. Ask questions in natural language
5. System retrieves relevant chunks and generates answer with sources

## Key Features

- PDF Upload & Processing - Upload multiple PDFs with automatic text extraction
- Intelligent Chunking - Split documents into semantic chunks (500 chars with 100 char overlap)
- Vector Embeddings - Generate 384-dimensional embeddings using sentence-transformers
- pgvector Search - Fast cosine similarity search over vector embeddings in PostgreSQL
- RAG Pipeline - Retrieve relevant context and generate answers using LLM
- Source Citations - Automatic attribution showing which documents/chunks were used
- FastAPI Backend - Production-ready REST API with CORS support
- Modern Frontend - Beautiful dark-themed UI with real-time chat interface
- Production Ready - Docker containerization for easy deployment

## RAG Architecture

PDF Documents -> Text Extraction (PyPDF2) -> Chunking (500 chars, 100 overlap) -> Embeddings (all-MiniLM-L6-v2, 384-dim) -> Vector Storage (Supabase pgvector) -> User Question -> Embed Question (same model) -> Similarity Search (cosine, top-5) -> Format Context + Prompt -> LLM Generation (Qwen3-8B via OpenRouter) -> Answer + Source Citations

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend Framework | FastAPI | REST API, request handling |
| LLM Provider | OpenRouter (Qwen3-8B) | Answer generation |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | 384-dim document embeddings |
| Vector Database | Supabase PostgreSQL + pgvector | Vector storage & similarity search |
| PDF Processing | PyPDF2 | Text extraction from PDFs |
| RAG Framework | LangChain | Prompt engineering, context injection |
| Frontend | HTML / CSS / JavaScript | User interface |
| Containerization | Docker | Production deployment |
| Deployment | Railway | Cloud hosting |

## Project Structure

ragforge-ai/
├── backend/
│   ├── main.py                 # FastAPI app, /chat & /upload endpoints
│   ├── embedding_service.py    # Embedding model (sentence-transformers)
│   ├── vector_db.py            # Supabase pgvector interface
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment variables (not in git)
├── frontend/
│   ├── index.html              # Main HTML interface
│   ├── style.css               # Dark theme styling
│   └── script.js               # Chat & upload logic
├── Dockerfile                  # Container configuration
├── .dockerignore               # Files to exclude from Docker
├── .gitignore                  # Git ignore rules
└── README.md                   # This file

## API Endpoints

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| GET | / | Health check | - | {status, model, documents_uploaded} |
| GET | /documents | List uploaded docs | - | {status, count, documents[]} |
| POST | /upload | Upload & process PDF | FormData (file) | {status, filename, chunk_count} |
| DELETE | /documents/{doc_id} | Delete document | - | {status, message} |
| POST | /chat | Ask question (RAG) | {question} | {status, answer, sources[]} |

Response Format (Chat):
{
  "status": "success",
  "answer": "Generated answer text...",
  "sources": [
    {"filename": "doc.pdf", "chunk_index": 3, "similarity": 0.871},
    {"filename": "doc.pdf", "chunk_index": 7, "similarity": 0.824}
  ]
}

## Environment Variables

Create .env file in backend/ directory:

OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=qwen/qwen3-8b
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_api_key_here

WARNING: Never commit .env to git! Use .gitignore to protect secrets.

## Local Setup

Prerequisites:
- Python 3.9+
- Git
- pip (Python package manager)

Steps:

1. Clone Repository
git clone https://github.com/ah8975644-commits/ragforge-ai.git
cd ragforge-ai

2. Create Virtual Environment
python -m venv venv
venv\Scripts\activate (Windows)
source venv/bin/activate (macOS/Linux)

3. Install Dependencies
cd backend
pip install -r requirements.txt

4. Configure Environment
Create .env file in backend/ folder
Add your API keys

5. Start Backend
cd backend
uvicorn main:app --reload
Backend runs on http://127.0.0.1:8000

6. Start Frontend (New Terminal)
cd frontend
python -m http.server 5000
Frontend runs on http://localhost:5000

7. Test
- Open http://localhost:5000
- Upload a PDF
- Ask a question
- See RAG answer with sources!

## Deployment (Railway)

Prerequisites:
- GitHub repository (push code first)
- Railway account (https://railway.app)

Steps:

1. Push Code to GitHub
git add .
git commit -m "Initial commit"
git push origin main

2. Create Railway Account
Go to https://railway.app
Sign up with GitHub

3. Deploy
New Project -> Deploy from GitHub
Select ragforge-ai repository
Railway auto-detects Dockerfile
Add environment variables in Railway dashboard
Deploy!

4. Add Environment Variables in Railway
OPENROUTER_API_KEY = your_key
OPENROUTER_MODEL = qwen/qwen3-8b
SUPABASE_URL = your_url
SUPABASE_KEY = your_key

5. Get Live URL
Dashboard -> Deployments -> Click latest
Copy domain URL
Share with world!

## Security

- CORS Enabled - Prevents unauthorized cross-origin requests
- Environment Variables - API keys stored securely, never in code
- No Authentication - Currently public (add JWT later if needed)
- .gitignore - Protects .env from accidental commits
- Supabase RLS - Disabled for simplicity (enable for multi-user)

## Current Status

Completed:
- FastAPI backend with RAG pipeline
- PDF upload, chunking, embedding
- Supabase pgvector integration
- LangChain RAG with source citations
- Modern dark-themed frontend
- Docker containerization
- Full end-to-end RAG workflow

In Progress:
- Railway deployment
- LinkedIn portfolio post

Future Improvements:
- Conversation memory (multi-turn chat)
- LangGraph for complex workflows
- User authentication (JWT)
- Rate limiting
- Document OCR (scanned PDFs)
- Streaming responses
- Monetization (API key system)

## License

Open source - feel free to use and modify!

## Author

Aly Barakode
AI Engineering Student | Full-Stack Developer
Building RAG systems and AI applications
GitHub: https://github.com/ah8975644-commits

Built with care for AI Engineering Portfolio