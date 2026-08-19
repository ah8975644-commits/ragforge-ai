from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import PyPDF2
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
import os
import requests


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(Path(__file__).parent / ".env")


# ============================================================
# IMPORT CUSTOM MODULES
# ============================================================

from embedding_service import embedding_service
from vector_db import vector_db


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "qwen/qwen3-8b"
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI()


# ============================================================
# CORS
# ============================================================

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

    allow_methods=[
        "GET",
        "POST",
        "DELETE",
        "OPTIONS"
    ],

    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Client-ID"
    ],
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class ChatRequest(BaseModel):
    question: str


class UploadResponse(BaseModel):
    status: str
    filename: str
    chunk_count: int


# ============================================================
# TEMPORARY IN-MEMORY DOCUMENT TRACKING
# ============================================================

uploaded_documents = {}


# ============================================================
# GET CLIENT ID
# ============================================================

def get_client_id(
    x_client_id: str = Header(default=None)
) -> str:

    """
    Get the temporary client ID sent by the frontend.

    Later this will be replaced with the authenticated
    Supabase user ID / JWT.
    """

    if not x_client_id:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Client-ID header"
        )

    return x_client_id


# ============================================================
# HEALTH / STATUS
# ============================================================

@app.get("/")
async def root():

    return {
        "status": "RAGForge AI Backend Running",

        "model": OPENROUTER_MODEL,

        "documents_uploaded":
            len(uploaded_documents)
    }


# ============================================================
# GET DOCUMENTS
# ============================================================

@app.get("/documents")
async def get_documents(
    x_client_id: str = Header(default=None)
):

    client_id = get_client_id(
        x_client_id
    )

    docs = []

    for doc_id, info in uploaded_documents.items():

        # Only show documents belonging
        # to this client.

        if info["user_id"] != client_id:
            continue

        docs.append({

            "doc_id": doc_id,

            "filename":
                info["filename"],

            "chunks":
                info["chunks"],

            "stored":
                info["stored"]
        })


    return {

        "status": "success",

        "count":
            len(docs),

        "documents":
            docs
    }


# ============================================================
# UPLOAD PDF
# ============================================================

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),

    x_client_id: str = Header(default=None)
):

    """
    Upload and process PDF.

    The PDF is associated with the temporary client ID.
    """

    # --------------------------------------------------------
    # GET CLIENT ID
    # --------------------------------------------------------

    client_id = get_client_id(
        x_client_id
    )


    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files allowed"
        )


    try:

        print(
            f"📤 Uploading: "
            f"{file.filename}"
        )

        print(
            f"👤 Client ID: "
            f"{client_id}"
        )


        # ====================================================
        # READ PDF
        # ====================================================

        pdf_content = await file.read()

        pdf_reader = PyPDF2.PdfReader(
            BytesIO(pdf_content)
        )


        # ====================================================
        # EXTRACT TEXT
        # ====================================================

        print(
            "📖 Extracting text from PDF..."
        )

        full_text = ""


        for page_num in range(
            len(pdf_reader.pages)
        ):

            page = pdf_reader.pages[
                page_num
            ]

            extracted_text = (
                page.extract_text()
                or ""
            )

            full_text += (
                extracted_text +
                "\n"
            )


        print(
            f"   Found "
            f"{len(pdf_reader.pages)} pages"
        )

        print(
            f"   Extracted "
            f"{len(full_text)} characters"
        )


        # ====================================================
        # CHUNK TEXT
        # ====================================================

        print(
            "✂️ Chunking text..."
        )

        chunk_size = 500

        overlap = 100

        chunks = []


        for i in range(
            0,
            len(full_text),
            chunk_size - overlap
        ):

            chunk = full_text[
                i:i + chunk_size
            ]


            if len(chunk.strip()) > 50:

                chunks.append(
                    chunk
                )


        print(
            f"   Created "
            f"{len(chunks)} chunks"
        )


        # ====================================================
        # GENERATE EMBEDDINGS
        # ====================================================

        print(
            "🧠 Creating embeddings..."
        )

        embeddings = (
            embedding_service
            .embed_batch(chunks)
        )


        print(
            f"   Generated "
            f"{len(embeddings)} embeddings "
            f"(384-dim each)"
        )


        # ====================================================
        # CREATE DOCUMENT ID
        # ====================================================

        doc_id = (
            file.filename
            .replace(".pdf", "")
            .replace(" ", "_")
        )


        # ====================================================
        # STORE IN SUPABASE
        # ====================================================

        print(
            "💾 Storing in Supabase pgvector..."
        )


        stored_count = (
            vector_db.store_chunks(

                user_id=client_id,

                doc_id=doc_id,

                filename=file.filename,

                chunks=chunks,

                embeddings=embeddings
            )
        )


        print(
            f"✅ Stored "
            f"{stored_count}/"
            f"{len(chunks)} chunks"
        )


        # ====================================================
        # TRACK DOCUMENT
        # ====================================================

        uploaded_documents[
            f"{client_id}:{doc_id}"
        ] = {

            "user_id":
                client_id,

            "doc_id":
                doc_id,

            "filename":
                file.filename,

            "chunks":
                len(chunks),

            "stored":
                stored_count
        }


        print(
            f"✅ Upload complete: "
            f"{file.filename}"
        )


        return {

            "status":
                "success",

            "filename":
                file.filename,

            "chunk_count":
                len(chunks)
        }


    except Exception as e:

        print(
            f"❌ Error uploading PDF: "
            f"{str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# DELETE DOCUMENT
# ============================================================

@app.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,

    x_client_id: str = Header(default=None)
):

    client_id = get_client_id(
        x_client_id
    )


    try:

        # Delete only this client's document.

        success = (
            vector_db.delete_document(
                user_id=client_id,
                doc_id=doc_id
            )
        )


        if not success:

            raise Exception(
                "Failed to delete document"
            )


        # Remove from temporary memory

        memory_key = (
            f"{client_id}:{doc_id}"
        )


        if memory_key in uploaded_documents:

            del uploaded_documents[
                memory_key
            ]


        return {

            "status":
                "success",

            "message":
                f"Document {doc_id} deleted"
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# CHAT / RAG ENDPOINT
# ============================================================

@app.post("/chat")
async def chat(
    request: ChatRequest,

    x_client_id: str = Header(default=None)
):

    """
    RAG-powered chat endpoint.

    IMPORTANT:
    Similarity search is performed ONLY against
    documents belonging to the current client.
    """

    client_id = get_client_id(
        x_client_id
    )


    question = (
        request.question.strip()
    )


    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )


    try:

        print(
            f"💬 Question from client: "
            f"{client_id}"
        )

        print(
            f"❓ {question}"
        )


        # ====================================================
        # EMBED QUESTION
        # ====================================================

        question_embedding = (
            embedding_service
            .embed_text(question)
        )


        # ====================================================
        # SEARCH SIMILAR CHUNKS
        # ====================================================

        results = (
            vector_db.search_similar(

                user_id=client_id,

                query_embedding=
                    question_embedding,

                limit=5
            )
        )


        print(
            f"🔎 Retrieved "
            f"{len(results)} relevant chunks"
        )


        # ====================================================
        # PREPARE SOURCES
        # ====================================================

        sources = []


        if results:

            for result in results:

                sources.append({

                    "filename":
                        result.get(
                            "filename",
                            "unknown"
                        ),

                    "doc_id":
                        result.get(
                            "doc_id",
                            ""
                        ),

                    "chunk_index":
                        result.get(
                            "chunk_index",
                            0
                        ),

                    "similarity":
                        round(
                            result.get(
                                "similarity",
                                0
                            ),
                            3
                        )
                })


        # ====================================================
        # BUILD CONTEXT
        # ====================================================

        if results:

            context = "\n\n".join([

                f"[Document: "
                f"{r.get('filename', 'unknown')}"
                f" | Chunk "
                f"{r.get('chunk_index', 0)}]\n"
                f"{r.get('chunk_text', '')}"

                for r in results
            ])

        else:

            context = ""


        # ====================================================
        # BUILD RAG PROMPT
        # ====================================================

        if context:

            rag_prompt = f"""
You are a helpful AI assistant.

Answer the user's question based ONLY
on the following document excerpts.

DOCUMENT EXCERPTS:

{context}

USER QUESTION:

{question}

INSTRUCTIONS:

- Answer based only on the provided excerpts.
- Be concise and accurate.
- Do not invent information.
- If the answer is not contained in the excerpts,
  say that the information was not found
  in the uploaded documents.
"""


        else:

            rag_prompt = f"""
The user has not provided relevant document
content for this question.

USER QUESTION:
{question}

Tell the user that the answer could not be
found in their uploaded documents.
"""


        # ====================================================
        # OPENROUTER / QWEN
        # ====================================================

        response = requests.post(

            "https://openrouter.ai/api/v1/chat/completions",

            headers={

                "Authorization":
                    f"Bearer {OPENROUTER_API_KEY}",

                "HTTP-Referer":
                    "https://ragforge-ai.vercel.app",

                "X-Title":
                    "RAGForge AI"
            },

            json={

                "model":
                    OPENROUTER_MODEL,

                "messages": [

                    {
                        "role":
                            "user",

                        "content":
                            rag_prompt
                    }

                ],

                "max_tokens":
                    1000
            }
        )


        # ====================================================
        # CHECK OPENROUTER RESPONSE
        # ====================================================

        if response.status_code != 200:

            raise Exception(
                f"OpenRouter error: "
                f"{response.text}"
            )


        data = response.json()


        answer = (
            data["choices"][0]
            ["message"]
            ["content"]
            .strip()
        )


        # ====================================================
        # RETURN ANSWER + SOURCES
        # ====================================================

        return {

            "status":
                "success",

            "answer":
                answer,

            "sources":
                sources
        }


    except Exception as e:

        print(
            f"❌ Chat error: "
            f"{str(e)}"
        )


        return {

            "status":
                "error",

            "answer":
                f"Error: {str(e)}",

            "sources":
                []
        }