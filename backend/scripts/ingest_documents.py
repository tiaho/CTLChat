"""Script to ingest documents into the vector database."""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger
from config import settings
from utils import setup_logging
from document_loader import load_documents
from vector_store import VectorStore


def main():
    """Main ingestion function."""
    # Setup logging
    setup_logging()

    logger.info("=" * 60)
    logger.info("CTLChat Document Ingestion Script")
    logger.info("=" * 60)

    # Check if data directory exists
    if not settings.data_dir.exists():
        logger.error(f"Data directory does not exist: {settings.data_dir}")
        logger.info(f"Please create the directory and add documents to it")
        return

    # Check if directory has files
    files = list(settings.data_dir.rglob('*.*'))
    if not files:
        logger.warning(f"No files found in {settings.data_dir}")
        logger.info("Please add documents to the curated_data directory")
        return

    logger.info(f"Found {len(files)} files in data directory")

    # Load documents
    logger.info("Loading and processing documents...")
    documents = load_documents()

    if not documents:
        logger.warning("No documents were loaded successfully")
        return

    logger.info(f"Loaded {len(documents)} document chunks")

    # Initialize vector store
    logger.info("Initializing vector store...")
    vector_store = VectorStore()

    # Check if collection already has documents
    existing_count = vector_store.get_collection_count()
    if existing_count > 0:
        logger.warning(f"Collection already contains {existing_count} documents")
        response = input("Do you want to reset the collection? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            logger.info("Resetting collection...")
            vector_store.reset_collection()
        else:
            logger.info("Appending to existing collection...")

    # Ingest documents
    logger.info("Ingesting documents into vector store...")
    vector_store.add_documents(documents)

    # Verify ingestion
    final_count = vector_store.get_collection_count()
    logger.info("=" * 60)
    logger.info(f"Ingestion complete!")
    logger.info(f"Total documents in vector store: {final_count}")
    logger.info(f"Collection name: {settings.collection_name}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nIngestion cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        sys.exit(1)
