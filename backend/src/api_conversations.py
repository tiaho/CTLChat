"""Example conversation endpoints for CTLChat API.

This module shows how to integrate the database module with your existing API.
You can merge these endpoints into your main api.py file.
"""
from typing import List, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from loguru import logger
from database import Database
from config import settings
import json


# Request/Response Models
class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    user_id: str
    org_id: str
    title: Optional[str] = None


class MessageCreate(BaseModel):
    """Request model for adding a message."""
    role: str
    content: str
    metadata: Optional[dict] = None


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
    metadata: Optional[str]


class ConversationWithMessages(ConversationResponse):
    """Response model for conversation with messages."""
    messages: List[MessageResponse]


# Initialize database (do this in your main api.py lifespan function)
db = Database(str(settings.db_path))


# Example endpoint functions (add these to your FastAPI app)

async def create_conversation(request: ConversationCreate) -> ConversationResponse:
    """Create a new conversation.

    POST /conversations

    Args:
        request: ConversationCreate request

    Returns:
        ConversationResponse with conversation details
    """
    try:
        # Verify user exists (optional)
        user = db.get_user(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {request.user_id} not found")

        # Create conversation
        conversation_id = db.create_conversation(
            user_id=request.user_id,
            org_id=request.org_id,
            title=request.title
        )

        # Get and return conversation
        conversation = db.get_conversation(conversation_id)
        return ConversationResponse(**conversation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_conversation(conversation_id: str) -> ConversationWithMessages:
    """Get a conversation with all its messages.

    GET /conversations/{conversation_id}

    Args:
        conversation_id: Conversation ID

    Returns:
        ConversationWithMessages with conversation and message details
    """
    try:
        conversation = db.get_conversation_with_messages(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ConversationWithMessages(**conversation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def list_user_conversations(
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[ConversationResponse]:
    """Get all conversations for a user.

    GET /users/{user_id}/conversations

    Args:
        user_id: User ID
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip

    Returns:
        List of ConversationResponse objects
    """
    try:
        conversations = db.get_user_conversations(user_id, limit, offset)
        return [ConversationResponse(**conv) for conv in conversations]

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def add_message_to_conversation(
    conversation_id: str,
    message: MessageCreate
) -> MessageResponse:
    """Add a message to a conversation.

    POST /conversations/{conversation_id}/messages

    Args:
        conversation_id: Conversation ID
        message: MessageCreate request

    Returns:
        MessageResponse with message details
    """
    try:
        # Verify conversation exists
        conversation = db.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Convert metadata dict to JSON string if present
        metadata_json = json.dumps(message.metadata) if message.metadata else None

        # Add message
        message_id = db.add_message(
            conversation_id=conversation_id,
            role=message.role,
            content=message.content,
            metadata=metadata_json
        )

        # Get all messages to find the one we just created
        messages = db.get_conversation_messages(conversation_id)
        created_message = next(msg for msg in messages if msg['message_id'] == message_id)

        return MessageResponse(**created_message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_conversation_title(conversation_id: str, title: str) -> ConversationResponse:
    """Update conversation title.

    PATCH /conversations/{conversation_id}

    Args:
        conversation_id: Conversation ID
        title: New title

    Returns:
        ConversationResponse with updated conversation
    """
    try:
        # Verify conversation exists
        conversation = db.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Update title
        db.update_conversation_title(conversation_id, title)

        # Get and return updated conversation
        updated_conversation = db.get_conversation(conversation_id)
        return ConversationResponse(**updated_conversation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def delete_conversation(conversation_id: str) -> dict:
    """Delete a conversation.

    DELETE /conversations/{conversation_id}

    Args:
        conversation_id: Conversation ID

    Returns:
        Success message
    """
    try:
        # Verify conversation exists
        conversation = db.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Delete conversation
        db.delete_conversation(conversation_id)

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Example of integrating with your existing chat endpoint
async def chat_with_conversation_save(
    query: str,
    user_id: str,
    org_id: str,
    conversation_id: Optional[str] = None,
    top_k: Optional[int] = None
) -> dict:
    """Chat endpoint that saves messages to database.

    This shows how to integrate conversation saving with your existing RAG chat.

    Args:
        query: User query
        user_id: User ID
        org_id: Organization ID
        conversation_id: Optional existing conversation ID
        top_k: Number of documents to retrieve

    Returns:
        Dict with response and conversation_id
    """
    try:
        # Create or get conversation
        if not conversation_id:
            # Create new conversation with first query as title
            title = query[:50] + "..." if len(query) > 50 else query
            conversation_id = db.create_conversation(
                user_id=user_id,
                org_id=org_id,
                title=title
            )
        else:
            # Verify conversation exists
            conversation = db.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

        # Save user message
        db.add_message(
            conversation_id=conversation_id,
            role="user",
            content=query
        )

        # Get conversation history for context
        messages = db.get_conversation_messages(conversation_id)
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        # TODO: Call your RAG engine here with conversation_history
        # For now, this is a placeholder
        # response = rag_engine.query(
        #     query=query,
        #     top_k=top_k,
        #     conversation_history=conversation_history[:-1],  # Exclude current message
        #     stream=False
        # )
        response = "This is a placeholder response"

        # Save assistant response
        db.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response
        )

        return {
            "conversation_id": conversation_id,
            "response": response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat with conversation save: {e}")
        raise HTTPException(status_code=500, detail=str(e))
