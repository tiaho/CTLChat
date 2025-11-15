"""FastAPI server for CTLChat RAG application."""
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger
from config import settings
from utils import setup_logging
from rag_engine import RAGEngine


# Request/Response Models
class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""
    query: str
    conversation_history: Optional[List[ChatMessage]] = None
    top_k: Optional[int] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    sources: List[dict] = []


class StatsResponse(BaseModel):
    """Statistics response model."""
    total_documents: int
    collection_name: str
    embedding_model: str


# Global RAG engine instance
rag_engine: Optional[RAGEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    global rag_engine

    # Startup
    setup_logging()
    logger.info("Starting CTLChat API server...")

    try:
        rag_engine = RAGEngine()
        logger.info("RAG Engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG Engine: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down CTLChat API server...")


# Create FastAPI app
app = FastAPI(
    title="CTLChat RAG API",
    description="Retrieval-Augmented Generation chatbot API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CTLChat RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    return {
        "status": "healthy",
        "vector_store_documents": rag_engine.get_store_stats()["total_documents"]
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get vector store statistics."""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    return rag_engine.get_store_stats()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for non-streaming responses.

    Args:
        request: Chat request with query and optional conversation history

    Returns:
        ChatResponse with answer and sources
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        logger.info(f"Received chat request: {request.query[:100]}...")

        # Convert conversation history to dict format
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Get retrieved documents for sources
        retrieved_docs = rag_engine.retrieve(request.query, top_k=request.top_k)

        # Generate response
        response = rag_engine.query(
            query=request.query,
            top_k=request.top_k,
            conversation_history=conversation_history,
            stream=False
        )

        # Format sources
        sources = [
            {
                "content": doc["content"][:200] + "...",  # Truncate for response
                "source": doc["metadata"].get("source", "Unknown"),
                "distance": doc.get("distance")
            }
            for doc in retrieved_docs
        ]

        return ChatResponse(response=response, sources=sources)

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Chat endpoint for streaming responses.

    Args:
        request: Chat request with query and optional conversation history

    Returns:
        StreamingResponse with generated text
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        logger.info(f"Received streaming chat request: {request.query[:100]}...")

        # Convert conversation history to dict format
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Generate streaming response
        response_stream = rag_engine.query(
            query=request.query,
            top_k=request.top_k,
            conversation_history=conversation_history,
            stream=True
        )

        return StreamingResponse(
            response_stream,
            media_type="text/plain"
        )

    except Exception as e:
        logger.error(f"Error processing streaming chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
