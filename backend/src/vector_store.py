"""Vector store operations using ChromaDB for RAG retrieval."""
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from loguru import logger
from config import settings


class VectorStore:
    """Manage vector embeddings and similarity search using ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB client and collection."""
        # Ensure the chroma_db directory exists
        settings.chroma_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "CTLChat RAG document embeddings"}
        )

        logger.info(f"Initialized ChromaDB collection: {settings.collection_name}")

    def add_documents(self, documents: List[Dict[str, any]]) -> None:
        """Add documents to the vector store.

        Args:
            documents: List of document dictionaries with 'content' and 'metadata'
        """
        if not documents:
            logger.warning("No documents to add")
            return

        # Prepare data for ChromaDB
        ids = []
        contents = []
        metadatas = []

        for i, doc in enumerate(documents):
            # Create unique ID
            doc_id = f"doc_{i}_{hash(doc['content'][:100])}"
            ids.append(doc_id)
            contents.append(doc['content'])
            metadatas.append(doc.get('metadata', {}))

        # Add to collection
        try:
            self.collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, any]]:
        """Search for similar documents using semantic similarity.

        Args:
            query: Search query text
            top_k: Number of results to return (defaults to settings.top_k_results)
            filter_metadata: Optional metadata filters

        Returns:
            List of retrieved documents with content, metadata, and relevance scores
        """
        top_k = top_k or settings.top_k_results

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter_metadata
            )

            # Format results
            retrieved_docs = []
            if results and results['documents'] and results['documents'][0]:
                for i, content in enumerate(results['documents'][0]):
                    retrieved_docs.append({
                        'content': content,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i] if results['ids'] else None
                    })

            logger.info(f"Retrieved {len(retrieved_docs)} documents for query")
            return retrieved_docs

        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    def delete_collection(self) -> None:
        """Delete the entire collection (use with caution)."""
        try:
            self.client.delete_collection(name=settings.collection_name)
            logger.warning(f"Deleted collection: {settings.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise

    def get_collection_count(self) -> int:
        """Get the number of documents in the collection.

        Returns:
            Number of documents in the collection
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            return 0

    def reset_collection(self) -> None:
        """Reset the collection (delete and recreate)."""
        try:
            self.delete_collection()
            self.collection = self.client.get_or_create_collection(
                name=settings.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "CTLChat RAG document embeddings"}
            )
            logger.info(f"Reset collection: {settings.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise


# Convenience functions
def create_vector_store() -> VectorStore:
    """Create and return a VectorStore instance."""
    return VectorStore()


def ingest_documents(documents: List[Dict[str, any]]) -> VectorStore:
    """Ingest documents into a new vector store.

    Args:
        documents: List of documents to ingest

    Returns:
        Initialized VectorStore instance
    """
    store = VectorStore()
    store.add_documents(documents)
    return store
