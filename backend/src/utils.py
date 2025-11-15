"""Utility functions for CTLChat RAG application."""
import sys
from pathlib import Path
from loguru import logger
from config import settings


def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    settings.logs_path.mkdir(parents=True, exist_ok=True)

    # Remove default logger
    logger.remove()

    # Add console logger
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )

    # Add file logger
    logger.add(
        settings.logs_path / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # Rotate daily at midnight
        retention="30 days",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    return logger


def clean_text(text: str) -> str:
    """Clean and normalize text content.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text with normalized whitespace
    """
    # Remove excessive whitespace
    text = " ".join(text.split())

    # Remove special characters if needed
    # text = re.sub(r'[^\w\s.,!?-]', '', text)

    return text.strip()


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk (characters)
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)

            if break_point > chunk_size * 0.5:  # Only break if it's not too early
                chunk = chunk[:break_point + 1]
                end = start + len(chunk)

        chunks.append(chunk.strip())
        start = end - overlap

    return [c for c in chunks if c]  # Filter empty chunks


def format_context(retrieved_docs: list[dict]) -> str:
    """Format retrieved documents into context for the LLM.

    Args:
        retrieved_docs: List of retrieved document chunks with metadata

    Returns:
        Formatted context string
    """
    if not retrieved_docs:
        return ""

    context_parts = []
    for i, doc in enumerate(retrieved_docs, 1):
        content = doc.get("content", "")
        source = doc.get("metadata", {}).get("source", "Unknown")
        context_parts.append(f"[Source {i}: {source}]\n{content}")

    return "\n\n".join(context_parts)


def chunk_markdown_by_separator(text: str, separator: str = "##") -> list[str]:
    """Split markdown text by a separator (e.g., ##).

    Args:
        text: Markdown text to chunk
        separator: Separator to split on (default: ##)

    Returns:
        List of text chunks split by separator
    """
    # Split by separator and clean up chunks
    chunks = text.split(separator)

    # Strip whitespace and filter out empty chunks
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

    return chunks


def get_file_extension(file_path: Path) -> str:
    """Get the file extension in lowercase.

    Args:
        file_path: Path to the file

    Returns:
        Lowercase file extension without the dot
    """
    return file_path.suffix.lower().lstrip('.')
