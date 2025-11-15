"""Document loading and processing for RAG pipeline."""
from pathlib import Path
from typing import List, Dict
import base64
import io
import pypdf
import docx
import markdown
from pdf2image import convert_from_path
from anthropic import Anthropic
from loguru import logger
from config import settings
from utils import clean_text, chunk_text, chunk_markdown_by_separator, get_file_extension


class DocumentLoader:
    """Load and process documents from various file formats."""

    def __init__(self, use_markdown_separator: bool = False):
        """Initialize the document loader.

        Args:
            use_markdown_separator: If True, split markdown files by ## separator
        """
        self.supported_extensions = {'.txt', '.pdf', '.docx', '.md'}
        self.use_markdown_separator = use_markdown_separator

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
        """Load content from a PDF file.

        First attempts regular text extraction. If the PDF appears to be scanned
        (very little text extracted), uses Claude's vision API for OCR.
        """
        text = []
        with open(file_path, 'rb') as f:
            pdf_reader = pypdf.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                text.append(page_text)

        combined_text = '\n'.join(text)

        # Check if this is likely a scanned PDF (very little text extracted)
        # Use a threshold of 100 characters total as indicator
        text_length = len(combined_text.strip())
        logger.info(f"Extracted {text_length} characters from PDF: {file_path.name}")

        if text_length < 100:
            logger.info(f"PDF appears to be scanned ({text_length} chars), attempting Claude vision OCR: {file_path.name}")
            try:
                return self._load_pdf_with_claude_vision(file_path)
            except Exception as e:
                logger.error(f"Claude vision OCR failed for {file_path.name}: {str(e)}")
                logger.info(f"Falling back to extracted text ({text_length} chars)")
                return combined_text

        logger.info(f"Using regular text extraction for {file_path.name}")
        return combined_text

    def _load_pdf_with_claude_vision(self, file_path: Path) -> str:
        """Extract text from a scanned PDF using Claude's vision API."""
        try:
            # Convert PDF pages to images
            logger.info(f"Converting PDF to images: {file_path.name}")
            images = convert_from_path(file_path)
            logger.info(f"Successfully converted {len(images)} pages to images")
        except Exception as e:
            error_msg = str(e)
            if "poppler" in error_msg.lower():
                raise Exception(
                    "Poppler is not installed or not in PATH. "
                    "Please install it:\n"
                    "  macOS: brew install poppler\n"
                    "  Linux: sudo apt-get install poppler-utils"
                )
            raise Exception(f"Failed to convert PDF to images: {error_msg}")

        # Initialize Anthropic client
        client = Anthropic(api_key=settings.anthropic_api_key)

        all_text = []

        for page_num, image in enumerate(images, 1):
            try:
                logger.info(f"Processing page {page_num}/{len(images)} with Claude vision")

                # Convert image to base64
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                # Use a vision-capable model (Sonnet supports vision)
                vision_model = "claude-sonnet-4-5-20250929"  # Known vision-capable model

                # Call Claude API with vision
                response = client.messages.create(
                    model=vision_model,
                    max_tokens=settings.max_tokens,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": img_base64,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "Extract all text from this document page. Preserve the structure and formatting as much as possible. Only return the extracted text, no additional commentary."
                                }
                            ],
                        }
                    ],
                )

                page_text = response.content[0].text
                all_text.append(f"--- Page {page_num} ---\n{page_text}")
                logger.info(f"Successfully extracted text from page {page_num}")

            except Exception as e:
                logger.error(f"Failed to process page {page_num}: {str(e)}")
                raise Exception(f"OCR failed on page {page_num}: {str(e)}")

        return '\n\n'.join(all_text)

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

    def load_directories(self, directories: List[Path] = None) -> List[Dict[str, any]]:
        """Load all supported documents from directories.

        Args:
            directories: List of directories to load documents from (defaults to data/ directory)

        Returns:
            List of dictionaries containing document chunks and metadata
        """
        # Default to main data directory (processes all subdirectories recursively)
        if directories is None:
            directories = [settings.data_dir]

        all_documents = []

        for directory in directories:
            logger.info(f"Loading documents from: {directory} (including all subdirectories)")

            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue

            documents = self._load_single_directory(directory)
            all_documents.extend(documents)

        logger.info(f"Total documents loaded: {len(all_documents)}")
        return all_documents

    def _load_single_directory(self, directory: Path) -> List[Dict[str, any]]:
        """Load all supported documents from a single directory.

        Args:
            directory: Directory to load documents from

        Returns:
            List of dictionaries containing document chunks and metadata
        """
        documents = []

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

                # Chunk the document based on file type and settings
                if extension == 'md' and self.use_markdown_separator:
                    # For markdown with markdown_separator flag, split by ## separator
                    chunks = chunk_markdown_by_separator(content)
                else:
                    # For other files, use character-based chunking
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

        logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents


# Convenience function
def load_documents(directories: List[Path] = None, use_markdown_separator: bool = False) -> List[Dict[str, any]]:
    """Load all documents from the specified directories.

    Args:
        directories: List of directories to load from (defaults to data/ directory, processes all subdirectories)
        use_markdown_separator: If True, split markdown files by ## separator

    Returns:
        List of document chunks with metadata
    """
    loader = DocumentLoader(use_markdown_separator=use_markdown_separator)
    return loader.load_directories(directories)
