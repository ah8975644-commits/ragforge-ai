from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import PyPDF2
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import json

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Import custom modules
from embedding_service import embedding_service
from vector_db import vector_db

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-8b")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# FastAPI app
app = FastAPI()

# CORS middleware - FIXED with correct Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://localhost:3000",
        "https://ragforge-ai.vercel.app",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Request/Response models
class ChatRequest(BaseModel):
    question: str

class UploadResponse(BaseModel):
    status: str
    filename: str
    chunk_count: int

# In-memory document tracking
uploaded_documents = {}

# ============ HEALTH & STATUS ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "status": "RAGForge AI Backend Running",
        "model": OPENROUTER_MODEL,
        "documents_uploaded": len(uploaded_documents)
    }

@app.get("/documents")
async def get_documents():
    """Get list of uploaded documents."""
    docs = []
    for doc_id, info in uploaded_documents.items():
        docs.append({
            "doc_id": doc_id,
            "filename": info["filename"],
            "chunks": info["chunks"],
            "stored": info["stored"]
        })
    
    return {
        "status": "success",
        "count": len(docs),
        "documents": docs
    }

# ============ UPLOAD ENDPOINT ============

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF file."""
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    try:
        print(f"📤 Uploading: {file.filename}")
        
        # Read PDF content
        pdf_content = await file.read()
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        
        # Extract text
        print("📖 Extracting text from PDF...")
        full_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            full_text += page.extract_text() + "\n"
        
        print(f"   Found {len(pdf_reader.pages)} pages")
        print(f"   Extracted {len(full_text)} characters")
        
        # Chunk text
        print("✂️  Chunking text...")
        chunk_size = 500
        overlap = 100
        chunks = []
        
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk = full_text[i:i + chunk_size]
            if len(chunk.strip()) > 50:  # Only keep meaningful chunks
                chunks.append(chunk)
        
        print(f"   Created {len(chunks)} chunks")
        
        # Generate embeddings
        print("🧠 Creating embeddings...")
        embeddings = embedding_service.embed_batch(chunks)
        print(f"   Generated {len(embeddings)} embeddings (384-dim each)")
        
        # Store in Supabase
        print("💾 Storing in Supabase pgvector...")
        doc_id = file.filename.replace(".pdf", "").replace(" ", "_")
        stored_count = vector_db.store_chunks(
            doc_id=doc_id,
            filename=file.filename,
            chunks=chunks,
            embeddings=embeddings
        )
        print(f"✅ Stored {stored_count}/{len(chunks)} chunks in Supabase")
        
        # Track in memory
        uploaded_documents[doc_id] = {
            "filename": file.filename,
            "chunks": len(chunks),
            "stored": stored_count
        }
        
        print(f"✅ Upload complete: {file.filename}")
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunk_count": len(chunks)
        }
    
    except Exception as e:
        print(f"❌ Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ DELETE ENDPOINT ============

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its chunks."""
    try:
        vector_db.delete_document(doc_id)
        
        if doc_id in uploaded_documents:
            del uploaded_documents[doc_id]
        
        return {
            "status": "success",
            "message": f"Document {doc_id} deleted"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ CHAT ENDPOINT (WITH SOURCES) ============

@app.post("/chat")
async def chat(request: ChatRequest):
    """RAG-powered chat endpoint with source citations."""
    question = request.question.strip()
    
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Embed the question
        question_embedding = embedding_service.embed_text(question)
        
        # Search for similar chunks
        results = vector_db.search_similar(question_embedding, limit=5)
        
        # Prepare sources (before building context)
        sources = []
        if results:
            for result in results:
                sources.append({
                    "filename": result.get("filename", "unknown"),
                    "chunk_index": result.get("chunk_index", 0),
                    "similarity": round(result.get("similarity", 0), 3)
                })
        
        # Build context from chunks (without filename)
        if results:
            context = "\n\n".join([
                f"[Chunk {r.get('chunk_index', 0)}]\n{r.get('chunk_text', '')}"
                for r in results
            ])
        else:
            context = ""
        
        # Build RAG prompt
        if context:
            rag_prompt = f"""You are a helpful AI assistant. Answer the user's question based on the following document excerpts:

DOCUMENT EXCERPTS:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
- Answer based only on the provided excerpts
- Be concise and accurate
- If the answer is not in the excerpts, say so clearly"""
        else:
            rag_prompt = f"USER QUESTION: {question}\n\nPlease answer this question."
        
        # Call OpenRouter/Qwen
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://ragforge-ai.vercel.app",
                "X-Title": "RAGForge AI"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": rag_prompt}],
                "max_tokens": 1000
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter error: {response.text}")
        
        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()
        
        # Return answer with sources
        return {
            "status": "success",
            "answer": answer,
            "sources": sources
        }
    
    except Exception as e:
        return {
            "status": "error",
            "answer": f"Error: {str(e)}",
            "sources": []
        }