"""Configuration management for CTLChat RAG application."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic API Configuration
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "claude-haiku-4-5-20251001")
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4096"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))

    # ChromaDB Configuration
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    collection_name: str = os.getenv("COLLECTION_NAME", "ctl_chat_docs")

    # Document Processing Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "5"))

    # Embedding Model
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # API Server Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: str = os.getenv("LOG_DIR", "./logs")

    # Paths
    @property
    def data_dir(self) -> Path:
        """Path to main data directory (processes all subdirectories recursively)."""
        return Path(__file__).parent.parent / "data"

    @property
    def chroma_path(self) -> Path:
        """Path to ChromaDB storage."""
        return Path(__file__).parent.parent / self.chroma_db_path

    @property
    def logs_path(self) -> Path:
        """Path to logs directory."""
        return Path(__file__).parent.parent / self.log_dir

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
