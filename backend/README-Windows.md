# CTLChat RAG Backend

A Retrieval-Augmented Generation (RAG) chatbot backend built with FastAPI, ChromaDB, and Claude.

## Features

- **Document Processing**: Supports TXT, PDF, DOCX, and Markdown files
- **Scanned PDF Support**: Automatic OCR using Claude's vision API for scanned documents
- **Vector Search**: Uses ChromaDB for efficient semantic search
- **Claude Integration**: Powered by Anthropic's Claude for response generation
- **REST API**: FastAPI server with streaming support
- **Configurable**: Environment-based configuration

## Project Structure
```
backend/
├── src/
│   ├── config.py            # Configuration management
│   ├── utils.py             # Utility functions
│   ├── document_loader.py   # Document processing
│   ├── vector_store.py      # ChromaDB operations
│   ├── rag_engine.py        # RAG core logic
│   └── api.py               # FastAPI server
├── scripts/
│   └── ingest_documents.py  # Document ingestion script
├── data/
│   ├── curated_data/        # Place your documents here
│   └── program_logs/        # Logs from previous programs
├── logs/                    # Application logs (not in git)
├── chroma_db/               # Vector database storage
├── venv/                    # Virtual environment (not in git)
├── requirements.txt         # Python dependencies
├── setup_venv.ps1           # Virtual environment setup script - powershell
├── setup_venv.sh            # Virtual environment setup script - bash
├── .env                     # Environment variables (not in git)
└── .env.example             # Environment template
```

## Setup

### 1. Install System Dependencies

**Python version:** Requires Python 3.11, 3.12, or 3.13 (not compatible with 3.14+)

For scanned PDF support (OCR), install poppler:

**Windows:**
```powershell
# Using Chocolatey
choco install poppler

# Or using Scoop
scoop install poppler
```


### 2. Set Up Virtual Environment

It's recommended to use a Python virtual environment to isolate dependencies:

**Option A: Automated Setup (recommended)**
```powershell
cd backend
.\setup_venv.ps1
```

This script will:
- Create a virtual environment in `backend\venv\`
- Upgrade pip
- Install all dependencies from `requirements.txt`

**Option B: Manual Setup**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Activate the virtual environment:**
```powershell
.\venv\Scripts\Activate.ps1
```

You'll know the virtual environment is active when you see `(venv)` in your terminal prompt.

**Deactivate when done:**
```powershell
deactivate
```

> **Note:** Make sure to activate the virtual environment before running any Python scripts or starting the server.

### 3. Configure Environment Variables

Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

Then edit `.env` and add your actual API key:
```powershell
ANTHROPIC_API_KEY=your_actual_api_key_here
```

Other settings can be adjusted as needed (see `.env.example` for all available options).

### 4. Add Documents

Place your documents anywhere in the `data\` directory. The system will recursively process all subdirectories. Supported formats:
- `.txt` - Plain text files
- `.pdf` - PDF documents (including scanned PDFs with automatic Claude vision OCR)
- `.docx` - Word documents
- `.md` - Markdown files

### 5. Ingest Documents

Run the ingestion script to process and index your documents:

**Basic ingestion (default chunking):**
```powershell
# Make sure virtual environment is activated first
.\venv\Scripts\Activate.ps1
python scripts\ingest_documents.py
```

**Markdown files with header separators:**
```powershell
# Split markdown files by ## headers instead of character-based chunking
python scripts\ingest_documents.py --markdown-separator
```

This will:
- Load all documents from `data\` directory (recursively processes all subdirectories)
- Chunk them into manageable pieces:
  - **Default**: Character-based chunking with overlap (all file types)
  - **With `--markdown-separator`**: Split markdown files by `##` headers, other files use default chunking
- Generate embeddings using sentence-transformers
- Store them in ChromaDB

### 6. Start the API Server
```powershell
# Make sure virtual environment is activated first
.\venv\Scripts\Activate.ps1
cd src
python api.py
```

Or using uvicorn directly:
```powershell
# Make sure virtual environment is activated first
.\venv\Scripts\Activate.ps1
cd src
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
```

### Get Statistics
```bash
GET /stats
```

### Chat (Non-streaming)
```bash
POST /chat
Content-Type: application/json

{
  "query": "What is the main topic of the documents?",
  "top_k": 5,
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

### Chat (Streaming)
```bash
POST /chat/stream
Content-Type: application/json

{
  "query": "Explain the key concepts",
  "top_k": 5
}
```

## Usage Examples

### Using PowerShell (Invoke-RestMethod)

**Simple query:**
```powershell
$body = @{
    query = "What are the main topics?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Streaming query:**
```powershell
$body = @{
    query = "Explain the key concepts"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/chat/stream" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    | Select-Object -ExpandProperty Content
```

### Using curl (if installed on Windows)

**Simple query:**
```powershell
curl -X POST "http://localhost:8000/chat" `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"What are the main topics?\"}'
```

**Streaming query:**
```powershell
curl -X POST "http://localhost:8000/chat/stream" `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"Explain the key concepts\"}' `
  --no-buffer
```

### Using Python
```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8000/chat",
    json={"query": "What are the main topics?"}
)
print(response.json())

# Streaming query
response = requests.post(
    "http://localhost:8000/chat/stream",
    json={"query": "Explain the key concepts"},
    stream=True
)
for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
    if chunk:
        print(chunk, end='', flush=True)
```

## Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `MODEL_NAME` | Claude model to use | claude-haiku-4-5-20251001 |
| `MAX_TOKENS` | Maximum response tokens | 4096 |
| `TEMPERATURE` | Response randomness (0-1) | 0.7 |
| `CHUNK_SIZE` | Document chunk size (default chunking only) | 1000 |
| `CHUNK_OVERLAP` | Overlap between chunks (default chunking only) | 200 |
| `TOP_K_RESULTS` | Number of results to retrieve | 5 |
| `EMBEDDING_MODEL` | Sentence transformer model | all-MiniLM-L6-v2 |
| `API_PORT` | API server port | 8000 |

## Development

### Adding New Document Types

To add support for new file formats, edit `document_loader.py`:

1. Add the extension to `supported_extensions`
2. Create a new `_load_<format>()` method
3. Update the `load_file()` method

### Customizing Document Chunking

The system supports multiple chunking strategies:

**Default chunking** (`utils.py:chunk_text`):
- Character-based with configurable size and overlap
- Attempts to break at sentence boundaries
- Used for all file types by default

**Markdown separator chunking** (`utils.py:chunk_markdown_by_separator`):
- Splits markdown files by `##` headers
- Enabled with `--markdown-separator` flag during ingestion
- Preserves logical document sections

To add custom chunking strategies:
1. Add new chunking function to `utils.py`
2. Update `document_loader.py` to conditionally use it
3. Add command-line flag to `ingest_documents.py` if needed

### Customizing Retrieval

Edit `vector_store.py` to modify:
- Search parameters
- Metadata filtering
- Embedding models

### Customizing Generation

Edit `rag_engine.py` to modify:
- System prompts
- Response formatting
- Context construction

## Troubleshooting

**No documents loaded:**
- Check that documents are in `data\curated_data\`
- Verify file formats are supported
- Check application logs in `logs\` directory

**API key errors:**
- Ensure `ANTHROPIC_API_KEY` is set in `.env`
- Verify the key is valid

**Empty responses:**
- Run ingestion script to populate vector database
- Check vector store has documents: `GET /stats`

## License

MIT
