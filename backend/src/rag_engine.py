"""RAG (Retrieval-Augmented Generation) engine for CTLChat."""
from typing import List, Dict, Optional, Iterator
import anthropic
from loguru import logger
from config import settings
from vector_store import VectorStore
from utils import format_context


class RAGEngine:
    """Core RAG logic combining retrieval and generation."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """Initialize the RAG engine.

        Args:
            vector_store: Optional VectorStore instance (creates new if not provided)
        """
        # Initialize Anthropic client
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment variables")

        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Initialize vector store
        self.vector_store = vector_store or VectorStore()

        logger.info("RAG Engine initialized")

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: User query
            top_k: Number of documents to retrieve

        Returns:
            List of retrieved documents
        """
        return self.vector_store.search(query, top_k=top_k)

    def generate(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate a response using Claude with retrieved context.

        Args:
            query: User query
            context: Retrieved context from documents
            conversation_history: Optional list of previous messages

        Returns:
            Generated response
        """
        # Build the system prompt
        system_prompt = """You are a helpful AI assistant. You answer questions based on the provided context from the knowledge base.

If the context contains relevant information, use it to provide accurate and detailed answers.
If the context doesn't contain enough information to answer the question, say so honestly.
Always be clear about what information comes from the provided context."""

        # Build the user message with context
        if context:
            user_message = f"""Context from knowledge base:
{context}

User question: {query}

Please answer the question based on the context provided above."""
        else:
            user_message = f"""No relevant context was found in the knowledge base.

User question: {query}

Please provide a helpful response, but note that this is based on general knowledge rather than specific documents."""

        # Build messages array
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current query
        messages.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=settings.model_name,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                system=system_prompt,
                messages=messages
            )

            # Extract response text
            answer = response.content[0].text
            logger.info("Generated response successfully")
            return answer

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def generate_stream(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[str]:
        """Generate a streaming response using Claude with retrieved context.

        Args:
            query: User query
            context: Retrieved context from documents
            conversation_history: Optional list of previous messages

        Yields:
            Chunks of the generated response
        """
        # Build the system prompt
        system_prompt = """You are a helpful AI assistant. You answer questions based on the provided context from the knowledge base.

If the context contains relevant information, use it to provide accurate and detailed answers.
If the context doesn't contain enough information to answer the question, say so honestly.
Always be clear about what information comes from the provided context."""

        # Build the user message with context
        if context:
            user_message = f"""Context from knowledge base:
{context}

User question: {query}

Please answer the question based on the context provided above."""
        else:
            user_message = f"""No relevant context was found in the knowledge base.

User question: {query}

Please provide a helpful response, but note that this is based on general knowledge rather than specific documents."""

        # Build messages array
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current query
        messages.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Call Claude API with streaming
            with self.client.messages.stream(
                model=settings.model_name,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                system=system_prompt,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            raise

    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False
    ) -> str | Iterator[str]:
        """Execute a complete RAG query: retrieve + generate.

        Args:
            query: User query
            top_k: Number of documents to retrieve
            conversation_history: Optional conversation history
            stream: Whether to stream the response

        Returns:
            Generated response (string or iterator if streaming)
        """
        logger.info(f"Processing RAG query: {query[:100]}...")

        # Retrieve relevant documents
        retrieved_docs = self.retrieve(query, top_k=top_k)

        # Format context
        context = format_context(retrieved_docs)

        logger.info(f"Retrieved {len(retrieved_docs)} documents")

        # Generate response
        if stream:
            return self.generate_stream(query, context, conversation_history)
        else:
            return self.generate(query, context, conversation_history)

    def get_store_stats(self) -> Dict[str, any]:
        """Get statistics about the vector store.

        Returns:
            Dictionary with store statistics
        """
        return {
            "total_documents": self.vector_store.get_collection_count(),
            "collection_name": settings.collection_name,
            "embedding_model": settings.embedding_model
        }
