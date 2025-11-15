"""FastAPI server for CTLChat RAG application."""
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger
from config import settings
from utils import setup_logging
from rag_engine import RAGEngine
from file_handler import process_file_upload
from database import Database
from query_preprocessing import preprocess_query, build_search_query
from conversation_summary import get_conversation_context_string
import json


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


class UploadResponse(BaseModel):
    """File upload response model."""
    message: str
    filename: str
    chunks_added: int
    total_documents: int


# Conversation models
class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    user_id: str
    org_id: Optional[str] = None
    title: Optional[str] = None


class MessageRequest(BaseModel):
    """Request model for sending a message."""
    user_id: str
    question: str
    selected_sources: Optional[List[str]] = None
    mode: str = "rag"  # rag, general_knowledge, web_search


class ConversationResponse(BaseModel):
    """Response model for conversation."""
    conversation_id: str
    user_id: str
    org_id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """Response model for message."""
    message_id: str
    conversation_id: str
    role: str
    content: str
    created_at: str


class ChatAnswerResponse(BaseModel):
    """Response for chat message."""
    answer: str
    sources_used: Optional[List[str]] = []
    full_context: Optional[str] = None
    chart: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None


# Global instances
rag_engine: Optional[RAGEngine] = None
db: Optional[Database] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    global rag_engine, db

    # Startup
    setup_logging()
    logger.info("Starting CTLChat API server...")

    try:
        # Initialize database
        db = Database(str(settings.db_path))
        logger.info("Database initialized successfully")

        # Initialize RAG engine
        rag_engine = RAGEngine()
        logger.info("RAG Engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
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


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    org_id: Optional[str] = Form(None),
    visibility: Optional[str] = Form("personal")
):
    """Upload and process a document file.

    Accepts document files, processes them, creates embeddings,
    and adds them to the vector store.

    Args:
        file: Uploaded file (.txt, .pdf, .docx, .md)
        user_id: User ID (for future multi-user support)
        org_id: Organization ID (for future multi-org support)
        visibility: Visibility setting ("personal" or "org-wide")

    Returns:
        UploadResponse with processing results
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        # Process the upload using the file handler
        result = process_file_upload(
            vector_store=rag_engine.vector_store,
            file=file,
            user_id=user_id,
            org_id=org_id,
            visibility=visibility
        )

        return UploadResponse(
            message="File uploaded and processed successfully",
            filename=result["filename"],
            chunks_added=result["chunks_added"],
            total_documents=result["total_documents"]
        )

    except HTTPException:
        # Re-raise HTTP exceptions from the handler
        raise
    except Exception as e:
        logger.error(f"Error in upload endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Conversation Endpoints
# ============================================================================

@app.get("/conversations")
async def list_conversations(user_id: str = Query(...)):
    """Get all conversations for a user.

    Args:
        user_id: User ID

    Returns:
        List of conversations
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        conversations = db.get_user_conversations(user_id, limit=100)
        return {"conversations": conversations}

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversations")
async def create_conversation(request: ConversationCreate):
    """Create a new conversation.

    Args:
        request: ConversationCreate request

    Returns:
        Conversation ID
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        # Get user to determine org_id if not provided
        org_id = request.org_id
        if not org_id:
            user = db.get_user(request.user_id)
            if user:
                org_id = user['org_id']
            else:
                # Default org for users not in database
                org_id = "org_sample_001"

        conversation_id = db.create_conversation(
            user_id=request.user_id,
            org_id=org_id,
            title=request.title or "New Conversation"
        )

        return {"conversation_id": conversation_id}

    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a conversation with all its messages.

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation with messages
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        conversation = db.get_conversation_with_messages(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, request: MessageRequest):
    """Send a message in a conversation and get AI response.

    Args:
        conversation_id: Conversation ID
        request: MessageRequest with question and options

    Returns:
        AI response with sources
    """
    if db is None or rag_engine is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        # Verify conversation exists
        conversation = db.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Save user message
        db.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.question
        )

        # Get conversation history (excluding the message we just added)
        all_messages = db.get_conversation_messages(conversation_id)
        previous_messages = all_messages[:-1]  # Exclude current user message

        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in previous_messages
        ]

        # Get organization name for context
        org = db.get_organization(conversation["org_id"])
        org_name = org["org_name"] if org else None

        # Generate response based on mode
        response_text = ""
        sources_used = []
        preprocessing_result = None

        if request.mode == "general_knowledge":
            # Use Claude without RAG
            from anthropic import Anthropic
            client = Anthropic(api_key=settings.anthropic_api_key)

            message_content = conversation_history + [{"role": "user", "content": request.question}]

            response = client.messages.create(
                model=settings.model_name,
                max_tokens=settings.max_tokens,
                messages=message_content
            )
            response_text = response.content[0].text

        elif request.mode == "web_search":
            # TODO: Implement web search functionality
            response_text = "Web search mode is not yet implemented."

        else:  # RAG mode
            # Build conversation context with summarization
            context_string = get_conversation_context_string(previous_messages, org_name)

            # Preprocess query with conversation context
            preprocessing_result = preprocess_query(
                query=request.question,
                org_name=org_name,
                conversation_context=context_string if context_string else None
            )

            # Build enhanced search query
            search_query = build_search_query(preprocessing_result)

            logger.info(f"Enhanced search query: {search_query}")

            # Get relevant documents using enhanced query
            retrieved_docs = rag_engine.retrieve(search_query, top_k=5)

            # Generate response with RAG using conversation context
            response_text = rag_engine.query(
                query=request.question,
                conversation_history=conversation_history,
                stream=False
            )

            # Extract sources
            sources_used = list(set([
                doc["metadata"].get("source", "Unknown")
                for doc in retrieved_docs
            ]))

            # Log query preprocessing results
            if preprocessing_result:
                logger.info(f"Query intent: {preprocessing_result['intent_type']}")
                logger.info(f"Related terms: {', '.join(preprocessing_result['related_terms'][:5])}")

        # Save assistant response
        db.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text
        )

        # Update conversation title if this is the first message
        if len(all_messages) == 1:  # Only user message exists
            title = request.question[:50] + "..." if len(request.question) > 50 else request.question
            db.update_conversation_title(conversation_id, title)

        return ChatAnswerResponse(
            answer=response_text,
            sources_used=sources_used,
            full_context=None,
            chart=None,
            data=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/organizations/{org_id}/sources")
async def get_organization_sources(org_id: str, user_id: str = Query(...)):
    """Get all document sources for an organization.

    This endpoint returns documents/sources uploaded to the vector store.

    Args:
        org_id: Organization ID
        user_id: User ID

    Returns:
        List of sources
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")

    try:
        # Get all documents from vector store
        # This is a simplified implementation - you may want to enhance this
        # to filter by org_id and user_id from metadata

        collection = rag_engine.vector_store.collection

        # Get all unique sources from the collection
        results = collection.get(include=['metadatas'])

        sources_dict = {}
        if results and results['metadatas']:
            for metadata in results['metadatas']:
                source = metadata.get('source', 'Unknown')
                visibility = metadata.get('visibility', 'personal')
                doc_user_id = metadata.get('user_id', '')
                doc_org_id = metadata.get('org_id', '')

                # Filter by org and user
                if doc_org_id == org_id or doc_user_id == user_id:
                    if source not in sources_dict:
                        sources_dict[source] = {
                            'source_id': source,
                            'name': source,
                            'visibility': visibility,
                            'user_id': doc_user_id,
                            'org_id': doc_org_id
                        }

        sources = list(sources_dict.values())

        return {"sources": sources}

    except Exception as e:
        logger.error(f"Error retrieving sources: {e}")
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
