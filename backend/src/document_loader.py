"""Document loading and processing for RAG pipeline."""
from pathlib import Path
from typing import List, Dict
import pypdf
import docx
import markdown
from loguru import logger
from config import settings
from utils import clean_text, chunk_text, get_file_extension


class DocumentLoader:
    """Load and process documents from various file formats."""

    def __init__(self):
        """Initialize the document loader."""
        self.supported_extensions = {'.txt', '.pdf', '.docx', '.md'}

    def load_file(self, file_path: Path) -> str:
        """Load content from a single file.

        Args:
            file_path: Path to the file to load

        Returns:
            Text content of the file

        Raises:
            ValueError: If file format is not supported
        """
        extension = get_file_extension(file_path)

        if extension == 'txt':
            return self._load_txt(file_path)
        elif extension == 'pdf':
            return self._load_pdf(file_path)
        elif extension == 'docx':
            return self._load_docx(file_path)
        elif extension == 'md':
            return self._load_markdown(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def _load_txt(self, file_path: Path) -> str:
        """Load content from a text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_pdf(self, file_path: Path) -> str:
        """Load content from a PDF file."""
        text = []
        with open(file_path, 'rb') as f:
            pdf_reader = pypdf.PdfReader(f)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return '\n'.join(text)

    def _load_docx(self, file_path: Path) -> str:
        """Load content from a Word document."""
        doc = docx.Document(file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

    def _load_markdown(self, file_path: Path) -> str:
        """Load content from a Markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        # Convert markdown to plain text (or keep markdown format)
        # html = markdown.markdown(md_content)
        # For simplicity, we'll keep the markdown format
        return md_content

    def load_directory(self, directory: Path = None) -> List[Dict[str, any]]:
        """Load all supported documents from a directory.

        Args:
            directory: Directory to load documents from (defaults to curated_data)

        Returns:
            List of dictionaries containing document chunks and metadata
        """
        directory = directory or settings.data_dir
        documents = []

        logger.info(f"Loading documents from: {directory}")

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return documents

        # Iterate through all files in directory
        for file_path in directory.rglob('*'):
            if not file_path.is_file():
                continue

            extension = get_file_extension(file_path)
            if f".{extension}" not in self.supported_extensions:
                logger.debug(f"Skipping unsupported file: {file_path}")
                continue

            try:
                logger.info(f"Processing file: {file_path.name}")

                # Load file content
                content = self.load_file(file_path)

                # Clean the text
                content = clean_text(content)

                # Chunk the document
                chunks = chunk_text(
                    content,
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap
                )

                # Create document entries with metadata
                for i, chunk in enumerate(chunks):
                    documents.append({
                        'content': chunk,
                        'metadata': {
                            'source': str(file_path.name),
                            'file_path': str(file_path),
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'file_type': extension
                        }
                    })

                logger.info(f"Processed {len(chunks)} chunks from {file_path.name}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        logger.info(f"Total documents loaded: {len(documents)}")
        return documents


# Convenience function
def load_documents(directory: Path = None) -> List[Dict[str, any]]:
    """Load all documents from the specified directory.

    Args:
        directory: Directory to load from (defaults to curated_data)

    Returns:
        List of document chunks with metadata
    """
    loader = DocumentLoader()
    return loader.load_directory(directory)
