"""Script to ingest documents into the vector database."""
import sys
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger
from config import settings
from utils import setup_logging
from document_loader import load_documents
from vector_store import VectorStore


def main(curated_data: bool = False, program_logs: bool = False):
    """Main ingestion function."""
    # Setup logging
    setup_logging()

    logger.info("=" * 60)
    logger.info("CTLChat Document Ingestion Script")
    logger.info("=" * 60)

    # Determine which directories to process and chunking strategy
    directories = []
    use_markdown_separator = False

    if curated_data and program_logs:
        # Both flags - process curated_data with markdown separator, then program_logs with normal chunking
        logger.info("Processing both curated_data (markdown) and program_logs (normal) directories")
        # Process curated_data first with markdown separator
        curated_dir = settings.data_dir / "curated_data"
        if curated_dir.exists():
            logger.info("Processing curated_data with markdown separator chunking")
            curated_docs = load_documents(directories=[curated_dir], use_markdown_separator=True)
        else:
            logger.warning(f"curated_data directory not found")
            curated_docs = []

        # Process program_logs with normal chunking
        logs_dir = settings.data_dir / "program_logs"
        if logs_dir.exists():
            logger.info("Processing program_logs with character-based chunking")
            logs_docs = load_documents(directories=[logs_dir], use_markdown_separator=False)
        else:
            logger.warning(f"program_logs directory not found")
            logs_docs = []

        documents = curated_docs + logs_docs

        if not documents:
            logger.warning("No documents were loaded successfully")
            return

        logger.info(f"Loaded {len(documents)} document chunks total")

    elif curated_data:
        # Only curated data - always use markdown separator
        directories = [settings.data_dir / "curated_data"]
        use_markdown_separator = True
        logger.info("Processing curated_data directory with markdown separator chunking")

        # Check if directory exists and has files
        if not directories[0].exists():
            logger.error(f"Directory does not exist: {directories[0]}")
            return

        files = list(directories[0].rglob('*.*'))
        if not files:
            logger.warning(f"No files found in {directories[0]}")
            return

        logger.info(f"Found {len(files)} files in curated_data directory")

        # Load documents
        documents = load_documents(directories=directories, use_markdown_separator=use_markdown_separator)

    elif program_logs:
        # Only program logs - use normal chunking
        directories = [settings.data_dir / "program_logs"]
        use_markdown_separator = False
        logger.info("Processing program_logs directory with character-based chunking")

        # Check if directory exists and has files
        if not directories[0].exists():
            logger.error(f"Directory does not exist: {directories[0]}")
            return

        files = list(directories[0].rglob('*.*'))
        if not files:
            logger.warning(f"No files found in {directories[0]}")
            return

        logger.info(f"Found {len(files)} files in program_logs directory")

        # Load documents
        documents = load_documents(directories=directories, use_markdown_separator=use_markdown_separator)

    else:
        # No flags - process both curated_data and program_logs with appropriate chunking for each
        logger.info("Processing both curated_data (markdown) and program_logs (normal) directories")

        # Process curated_data with markdown separator
        curated_dir = settings.data_dir / "curated_data"
        if curated_dir.exists():
            logger.info("Processing curated_data with markdown separator chunking")
            curated_docs = load_documents(directories=[curated_dir], use_markdown_separator=True)
        else:
            logger.warning(f"curated_data directory not found")
            curated_docs = []

        # Process program_logs with normal chunking
        logs_dir = settings.data_dir / "program_logs"
        if logs_dir.exists():
            logger.info("Processing program_logs with character-based chunking")
            logs_docs = load_documents(directories=[logs_dir], use_markdown_separator=False)
        else:
            logger.warning(f"program_logs directory not found")
            logs_docs = []

        documents = curated_docs + logs_docs

        if not documents:
            logger.warning("No documents were loaded successfully")
            return

        logger.info(f"Loaded {len(documents)} document chunks total")

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
    parser = argparse.ArgumentParser(
        description="Ingest documents into the CTLChat vector database"
    )
    parser.add_argument(
        "--curated-data",
        action="store_true",
        help="Process only data/curated_data directory (markdown files with ## separator chunking)"
    )
    parser.add_argument(
        "--program-logs",
        action="store_true",
        help="Process only data/program_logs directory (character-based chunking)"
    )

    args = parser.parse_args()

    try:
        main(
            curated_data=args.curated_data,
            program_logs=args.program_logs
        )
    except KeyboardInterrupt:
        logger.info("\nIngestion cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        sys.exit(1)
